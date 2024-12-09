import os
from pathlib import Path

import numpy as np

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from tqdm import tqdm

import istarmap # apply patch to allow tqdm on starmap
from multiprocessing import Pool, Lock


import pandas as pd




BINVOX_MIMETYPE = 'application/octet-stream'
STL_MIMETYPE = 'application/vnd.ms-pki.stl'
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

ENTRIES_PER_PAGE = 1000

MAX_PAGES = 50 # how many pages to go per folder, set to 1 for testing

NUM_WORKERS = 60 # just put the max that works?? don't know what number is maximum for a given architecture, but can find by doubling

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']

script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute paths
data_dir = os.path.join(script_dir, "../data")
PARENTS = pd.read_csv(os.path.join(data_dir, "model_links/parents.csv"))
STL_FOLDER_ID = pd.read_csv(os.path.join(data_dir, "model_links/stl_files.csv"), index_col=0)
BINVOX_DEFAULT_FOLDER_ID = pd.read_csv(os.path.join(data_dir, "model_links/default_res.csv"), index_col=0)
BINVOX_64_FOLDER_ID = pd.read_csv(os.path.join(data_dir, "model_links/64_res.csv"), index_col=0)
NAME_TO_MODEL_ID = pd.read_csv(os.path.join(data_dir, "id_data.csv"), index_col=1)

NUM_DOWNLOAD_RETRIES = 10

EST_SIZES = {
    "parts_0_files_1_to_3950": 3950,
    "parts_0_files_3951_to_5450": 1500,
    "parts_0_files_5451_to_9606": 4156,
    "parts_1_files_1_to_2500": 2500,
    "parts_1_files_2501_to_7500": 5000,
    "parts_1_files_7501_to_11227": 3727,
    "parts_2_files_1_to_3500": 3500,
    "parts_2_files_3501_to_7000": 4000,
    "parts_2_files_7001_to_11076": 3576,
    "parts_3_files_1_to_5500": 5500,
    "parts_3_files_5501_to_10844": 5344,
    "parts_4_files_1_to_5500": 5500,
    "parts_4_files_5501_to_8000": 2499,
    "parts_4_files_8001_to_10154": 2143,
    "parts_5_files_1_to_3000": 3000,
    "parts_5_files_3001_to_5500": 2499,
    "parts_5_files_5501_to_9000": 3499,
    "parts_5_files_9001_to_11289": 2289,
    "parts_6_files_1_to_3500": 3500,
    "parts_6_files_3501_to_7000": 3499,
    "parts_6_files_7001_to_10567": 3567,
    "parts_7_files_1_to_3667": 3667,
    "parts_7_files_3668_to_7334": 3667,
    "parts_7_files_7335_to_11046": 3707,
    "parts_8_files_1_to_3500": 3500,
    "parts_8_files_3501_to_7000": 3499,
    "parts_8_files_7001_to_10222": 3222,
    "parts_10": 11000
}

def load_google_api_key(cwd):
    # load api key from .env
    with open(os.path.join(cwd, ".env"), "r") as f:
        for line in f.readlines():
            if line.startswith("GOOGLE_API_KEY"):
                return line.split("=")[1].strip()

def token_login():

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


# download files in folderName locally
def download_all_binvox_stl_files_in(folderName, service):
    # get folderId of each folder type
    binvox_default_folderId = BINVOX_DEFAULT_FOLDER_ID.loc[folderName, "folderId"]
    stl_folderId = STL_FOLDER_ID.loc[folderName, "folderId"]

    # print(f'foldername: {folderName}, binvox: {binvox_default_folderId}, stl: {stl_folderId}')
    
    # 6 because one for each rotation
    estimated_limit = (6 * EST_SIZES[folderName]) // ENTRIES_PER_PAGE
    
    # Source default_res binvox files
    print(f"Sourcing default_res binvox files for {folderName}...")
    binvox_list = [(folderName, binvox_file, service, BINVOX_MIMETYPE) for binvox_file in get_all_files_of_type(binvox_default_folderId, service, BINVOX_MIMETYPE, estimated_limit=estimated_limit)]

    # Source stl files
    print(f"Sourcing stl files for {folderName}...")
    stl_list = [(folderName, stl_file, service, STL_MIMETYPE) for stl_file in get_all_files_of_type(stl_folderId, service, STL_MIMETYPE, estimated_limit=estimated_limit)]

    # (implement later) download 64_res binvox files

    all_list = binvox_list + stl_list

    print(f"Starting parallelized downloading for {folderName}...")
    with Pool(NUM_WORKERS) as p:
        for _ in tqdm(p.istarmap(download_file, all_list), total=len(all_list)):
            pass
    
    
# returns list of files in folderId that match mimeType
def get_all_files_of_type(folderId, service, mimeType, pageLimit=MAX_PAGES, estimated_limit=0):

    direct_files = get_files_directly_in(folderId, service)
    results = [f for f in direct_files.get('files', []) if f['mimeType'] == mimeType]
    
    
    with tqdm(total=estimated_limit) as pbar:
        i = 0
        while ('nextPageToken' in direct_files and i < pageLimit):
            pbar.update(1)

            direct_files = get_files_directly_in(folderId, service, nextPageToken=direct_files['nextPageToken'])
            results += [f for f in direct_files.get('files', []) if f['mimeType'] == mimeType]
            
            i += 1
        pbar.update(1)
    return results

# helper function for get_all_files_of_type()
def get_files_directly_in(folderId, service, mimeType=None, nextPageToken=None):
    # Get folder metadata
    folder_metadata = service.files().get(
        fileId=folderId,
        fields="id, name, mimeType, driveId, parents",
        supportsAllDrives=True
    ).execute()
    
    # Determine if the folder is in a shared drive
    driveId = folder_metadata.get('driveId', None)
    
    query = f"'{folderId}' in parents"
    if mimeType:
        query += f" and mimeType = '{mimeType}'"  
    results = [] 
    try:
        # Make the request to the Google Drive API
        if driveId:
            results = service.files().list(
                q=query,
                corpora="drive",  # Specifies that the query is for shared drive or personal drive
                driveId=driveId if driveId else None,  # Pass driveId if it's in a shared drive
                includeItemsFromAllDrives=True,  # Include items from all drives (shared or personal)
                supportsAllDrives=True,  # Ensure the API handles shared drives correctly
                pageSize=ENTRIES_PER_PAGE,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=nextPageToken
            ).execute()
        else:
            # If the folder is not in a shared drive, use the default behavior for personal drives
            results = service.files().list(
                q=query,
                supportsAllDrives=True,
                pageSize=ENTRIES_PER_PAGE,
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=nextPageToken
            ).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
    
    return results



# download fileName belonging to folderName (todo: change fileName when claling earlier)
def download_file(folderName, file, service, mimeType):
    if mimeType == BINVOX_MIMETYPE:
            file_type = "binvox"
    elif mimeType == STL_MIMETYPE:
            file_type = "stl"

    try:
        # name file the model id when downloading
        fileNameNoExtension = os.path.splitext(file['name'])[0]
        file_name = NAME_TO_MODEL_ID.loc[fileNameNoExtension, "id"]
    except KeyError:
        print(f"WARNING: Could not find model id for {file['name']}")
        return
        
    path = os.path.join(data_dir, file_type, folderName)
    if not os.path.exists(path):
        os.makedirs(path)
    
    request = service.files().get_media(fileId=file['id'])
    file_path = os.path.join(path, f"{file_name}.{file_type}")
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            # print(f"File {file_path} already exists")
            return
        else:
            print(f"File {file_path} exists but is empty, redownloading")
            os.remove(file_path)

    # add progress bar to download using tqdm
    with open(file_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk(num_retries=NUM_DOWNLOAD_RETRIES)


def get_folder_details(folder_id, service):
    try:
        folder_details = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType", 
            supportsAllDrives = True
        ).execute()
        return folder_details
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    
# done 
def main():
    
    # get credentials
    os.chdir(os.path.dirname(__file__))
    creds = token_login()

    # try
    try:
        service = build('drive', 'v3', credentials=creds)

        # iterate through each folder
        for _, row in PARENTS.iterrows():
            folderName = row['folderName']
            print(f"Starting {folderName}")
            download_all_binvox_stl_files_in(folderName, service)
            print(f"Done with {folderName}")
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    os.chdir(Path(os.path.dirname(__file__)).parents[0])
    main()