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


# load in the model id to stl and binvox id data
STL_TO_MODEL_ID = pd.read_csv("data/id_data.csv", index_col=1)
BINVOX_TO_MODEL_ID = pd.read_csv("data/id_data.csv", index_col=2)

BINVOX_SEARCH_KEY = "binvox_default_res"
STL_SEARCH_KEY = "rotated_stl_files"

NUM_DOWNLOAD_RETRIES = 10

ALL_FILE_FOLDERS = {
    # "URAP3D_STL": "1P0k67JaVkJRyFysUC_G8bKmRQQD_TKhq",
    # "CAD_PARTS_FOLDER": "1kvid8nlRhSFrnIzrZbjt5uOOuEixPBpN",
    # done: "PARTS_0_1_3950": "1rIlKhyHHyQ55RW8igH7ywnH0hXMLDwA_",
    # done: "PARTS_0_3951_5450": "1cKpVz3Vol2F8-i-V6ixnGkH94Al8VsjP",
    # done: "PARTS_0_5451_9606": "1CkJ30EDPfz8g0okPQPW19vkoqzdClYg8",
    # done: "PARTS_1_1_2500": "1j_J4PxkVZlfP7kqhP4JwyUG29bYVLbNJ",
    # done: "PARTS_1_2501_7500": "155SmkUlp2Z8nVb_VjUgoTNPRMO1jl9gQ",
    # done: "PARTS_1_7501_11227": "1ZtDlxIVOq_B6gbryrtXZTQXJpv3bodEv",
    # done: "PARTS_2_1_3500": "1Ju7G3RB-KLtC4i8drcGdN2YEcUczueov",
    # done: "PARTS_2_3501_7500": "1kUIWVdyryIcETdOQik29T1DPVZAWJ9-a",
    # done: "PARTS_2_7501_11076": "1ZwfiDKMlHZgpgZOOJhqBUwQnBFjXQhZd",
    # done: "PARTS_3_1_5500": "19rsrWC1dmBtCD9uPJCC5QdwOWD7VYeY7",
    # done: "PARTS_3_5501_10844": "1GOTtPLaxOlAguBdNuKfpeLn8UuA5OCxA",
    # done: "PARTS_4_1_5500": "1xXbNZ2fGW_9wz3ezM84ckqCq91cTySwR",
    # done: "PARTS_4_5501_8000": "1I5fMkCzS26gT4yjnd5VIB80ga2glWzNc",
    # done: "PARTS_4_8001_10154": "1RlXw5gWgBt9Ce2nHgrdPy-1i5dCPKf-7",
    # done: "PARTS_5_1_3000": "1AXASF26UG9-fXAHCa9mLXHk-WhjpWrVB",
    # done: "PARTS_5_3001_5500": "1JZes4v9qIU9QdaKaU8qtDkLBaY2jZzIe",
    # done: "PARTS_5_5501_9000": "1MhR-Gr8Gid_H2yFBsH89H5L3MCMKMKng",
    # done: "PARTS_5_9001_11289": "1Z3DbNC7yEI-41m3sG04EAy0ifaOMVMK1",
    # done: "PARTS_6_1_3500": "17Tomwp9gSCGL54tORcxBYTIq08hlVbVJ",
    # done: "PARTS_6_3501_7000": "1mpPRuCfFv2A_Xv6e-LFdD1sMKrUt-pjK",
    # done: "PARTS_6_7001_10567": "1F-C_PwR6vsk90cXKVtaY2bOdx_ZLoaKB",
    # done: "PARTS_7_1_3667": "1u4y9Mjpg3NM-SI27dr5tMjVUwB6ibiSG",
    # done: "PARTS_7_3668_7334": "1mo6_so7q8fX4LmcWiiL3mao_uqMh1j-p",
    # done: "PARTS_7_7335_11046": "1ZA6E3t6ayo5bOMBMVaZgBqbOCh5eLij5",
    # done: "PARTS_8_1_3500": "1JInIBDb4icrMGPMk4bladLpNmTiDTW_m",
    # done: "PARTS_8_3501_7000": "1M3aFmYbn_msl7VEUV8grx70-5vXM8Q7U",
    # done: "PARTS_8_7001_10222": "1qjyaoedbdDHw5lLoWgyHIl1f91dwFJI0",
    # done, but kinda small?: "PARTS_10": "1wUmkgUvyEZ-u_LAcOR9bqSoMU-yWS-dh",
}

EST_SIZES = {
    "1rIlKhyHHyQ55RW8igH7ywnH0hXMLDwA_": 3950,
    "1cKpVz3Vol2F8-i-V6ixnGkH94Al8VsjP": 1500,
    "1CkJ30EDPfz8g0okPQPW19vkoqzdClYg8": 4156,
    "1j_J4PxkVZlfP7kqhP4JwyUG29bYVLbNJ": 2500,
    "155SmkUlp2Z8nVb_VjUgoTNPRMO1jl9gQ": 5000,
    "1ZtDlxIVOq_B6gbryrtXZTQXJpv3bodEv": 3727,
    "1Ju7G3RB-KLtC4i8drcGdN2YEcUczueov": 3500,
    "1kUIWVdyryIcETdOQik29T1DPVZAWJ9-a": 4000,
    "1ZwfiDKMlHZgpgZOOJhqBUwQnBFjXQhZd": 3576,
    "19rsrWC1dmBtCD9uPJCC5QdwOWD7VYeY7": 5500,
    "1GOTtPLaxOlAguBdNuKfpeLn8UuA5OCxA": 5344,
    "1xXbNZ2fGW_9wz3ezM84ckqCq91cTySwR": 5500,
    "1I5fMkCzS26gT4yjnd5VIB80ga2glWzNc": 2499,
    "1RlXw5gWgBt9Ce2nHgrdPy-1i5dCPKf-7": 2143,
    "1AXASF26UG9-fXAHCa9mLXHk-WhjpWrVB": 3000,
    "1JZes4v9qIU9QdaKaU8qtDkLBaY2jZzIe": 2499,
    "1MhR-Gr8Gid_H2yFBsH89H5L3MCMKMKng": 3499,
    "1Z3DbNC7yEI-41m3sG04EAy0ifaOMVMK1": 2289,
    "17Tomwp9gSCGL54tORcxBYTIq08hlVbVJ": 3500,
    "1mpPRuCfFv2A_Xv6e-LFdD1sMKrUt-pjK": 3499,
    "1F-C_PwR6vsk90cXKVtaY2bOdx_ZLoaKB": 3567,
    "1u4y9Mjpg3NM-SI27dr5tMjVUwB6ibiSG": 3667,
    "1mo6_so7q8fX4LmcWiiL3mao_uqMh1j-p": 3667,
    "1ZA6E3t6ayo5bOMBMVaZgBqbOCh5eLij5": 3707,
    "1JInIBDb4icrMGPMk4bladLpNmTiDTW_m": 3500,
    "1M3aFmYbn_msl7VEUV8grx70-5vXM8Q7U": 3499,
    "1qjyaoedbdDHw5lLoWgyHIl1f91dwFJI0": 3222,
    "1wUmkgUvyEZ-u_LAcOR9bqSoMU-yWS-dh": 11000
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


def get_files_directly_in(folderId, service, mimeType=None, nextPageToken=None):

    # Call the Drive v3 API
    query = f"'{folderId}' in parents"
    if mimeType:
        query += f" and mimeType = '{mimeType}'"
    results = []
    try:
        results = service.files().list(
            pageSize=ENTRIES_PER_PAGE,
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=nextPageToken).execute()
    except HttpError:
        print(f"Error for token {nextPageToken}")

    return results


def download_all_binvox_stl_files_in(folderId, service):
    print("Finding source folder in Google Drive...")
    direct_files = get_files_directly_in(folderId, service)
    binvox_folder = [f for f in direct_files.get('files', []) if f['mimeType'] == FOLDER_MIMETYPE and BINVOX_SEARCH_KEY in f['name']][0]
    stl_folder = [f for f in direct_files.get('files', []) if f['mimeType'] == FOLDER_MIMETYPE and STL_SEARCH_KEY in f['name']][0]
    print("Done!\n")


    # 6 because one for each rotation
    estimated_limit = (6 * EST_SIZES[folderId]) // ENTRIES_PER_PAGE

    print("Sourcing binvox files...")
    binvox_list = [(folderId, binvox_file['id'], service, BINVOX_MIMETYPE) for binvox_file in get_all_files_of_type(binvox_folder['id'], service, BINVOX_MIMETYPE, estimated_limit=estimated_limit)]
    
    print("Sourcing stl files...")
    stl_list = [(folderId, stl_file['id'], service, STL_MIMETYPE) for stl_file in get_all_files_of_type(stl_folder['id'], service, STL_MIMETYPE, estimated_limit=estimated_limit)]
    
    all_list = binvox_list + stl_list
    
    print("Starting parallelized downloading...")
    with Pool(NUM_WORKERS) as p:
        for _ in tqdm(p.istarmap(download_file, all_list), total=len(all_list)):
            pass

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

def download_file(parent_folder_id, file_id, service, mimeType):
    try:
        if mimeType == BINVOX_MIMETYPE:
            file_type = "binvox"
            file_name = BINVOX_TO_MODEL_ID.loc[file_id, "id"]
        elif mimeType == STL_MIMETYPE:
            file_type = "stl"
            file_name = STL_TO_MODEL_ID.loc[file_id, "id"]
    except KeyError:
        print(f"WARNING: Could not find model id for {file_id}")
        return
        
    path = os.path.join("data", file_type, parent_folder_id)
    
    if not os.path.exists(path):
        os.makedirs(path)
    
    request = service.files().get_media(fileId=file_id)

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
        # print(f"Downloading {file_path}")
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk(num_retries=NUM_DOWNLOAD_RETRIES)

def main():
    
    os.chdir(os.path.dirname(__file__))
    creds = token_login()

    try:
        service = build('drive', 'v3', credentials=creds)
        
        for folder in ALL_FILE_FOLDERS.keys():
            print(f"Starting {folder}")
            download_all_binvox_stl_files_in(ALL_FILE_FOLDERS[folder], service)
            print(f"Done with {folder}")
            
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    os.chdir(Path(os.path.dirname(__file__)).parents[0])
    main()
