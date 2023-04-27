import os.path
from typing import List
import asyncio

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from multiprocessing import Pool
from prisma import Prisma

ALL_FILE_FOLDERS = {
    "URAP3D_STL": "1P0k67JaVkJRyFysUC_G8bKmRQQD_TKhq",
    "CAD_PARTS_FOLDER": "1kvid8nlRhSFrnIzrZbjt5uOOuEixPBpN",
    "PARTS_0_1_3950": "1rIlKhyHHyQ55RW8igH7ywnH0hXMLDwA_",
    "PARTS_0_3951_5450": "1cKpVz3Vol2F8-i-V6ixnGkH94Al8VsjP",
    "PARTS_0_5451_9606": "1CkJ30EDPfz8g0okPQPW19vkoqzdClYg8",
    "PARTS_1_1_2500": "1j_J4PxkVZlfP7kqhP4JwyUG29bYVLbNJ",
    "PARTS_1_2501_7500": "155SmkUlp2Z8nVb_VjUgoTNPRMO1jl9gQ",
    "PARTS_1_7501_11227": "1ZtDlxIVOq_B6gbryrtXZTQXJpv3bodEv",
    "PARTS_2_1_3500": "1Ju7G3RB-KLtC4i8drcGdN2YEcUczueov",
    "PARTS_2_3501_7500": "1kUIWVdyryIcETdOQik29T1DPVZAWJ9-a",
    "PARTS_2_7501_11076": "1ZwfiDKMlHZgpgZOOJhqBUwQnBFjXQhZd",
    "PARTS_3_1_5500": "19rsrWC1dmBtCD9uPJCC5QdwOWD7VYeY7",
    "PARTS_3_5501_10844": "1GOTtPLaxOlAguBdNuKfpeLn8UuA5OCxA",
    "PARTS_4_1_5500": "1xXbNZ2fGW_9wz3ezM84ckqCq91cTySwR",
    "PARTS_4_5501_8000": "1I5fMkCzS26gT4yjnd5VIB80ga2glWzNc",
    "PARTS_4_8001_10154": "1RlXw5gWgBt9Ce2nHgrdPy-1i5dCPKf-7",
    "PARTS_5_1_3000": "1AXASF26UG9-fXAHCa9mLXHk-WhjpWrVB",
    "PARTS_5_3001_5500": "1JZes4v9qIU9QdaKaU8qtDkLBaY2jZzIe",
    "PARTS_5_5501_9000": "1MhR-Gr8Gid_H2yFBsH89H5L3MCMKMKng",
    "PARTS_5_9001_11289": "1Z3DbNC7yEI-41m3sG04EAy0ifaOMVMK1",
    "PARTS_6_1_3500": "17Tomwp9gSCGL54tORcxBYTIq08hlVbVJ",
    "PARTS_6_3501_7000": "1mpPRuCfFv2A_Xv6e-LFdD1sMKrUt-pjK",
    "PARTS_6_7001_10567": "1F-C_PwR6vsk90cXKVtaY2bOdx_ZLoaKB",
    "PARTS_7_1_3667": "1u4y9Mjpg3NM-SI27dr5tMjVUwB6ibiSG",
    "PARTS_7_3668_7334": "1mo6_so7q8fX4LmcWiiL3mao_uqMh1j-p",
    "PARTS_7_7335_11046": "1ZA6E3t6ayo5bOMBMVaZgBqbOCh5eLij5",
    "PARTS_8_1_3500": "1JInIBDb4icrMGPMk4bladLpNmTiDTW_m",
    "PARTS_8_3500_7000": "1M3aFmYbn_msl7VEUV8grx70-5vXM8Q7U",
    "PARTS_8_7001_10222": "1qjyaoedbdDHw5lLoWgyHIl1f91dwFJI0",
    "PARTS_10": "1wUmkgUvyEZ-u_LAcOR9bqSoMU-yWS-dh",
}

BINVOX_MIMETYPE = 'application/octet-stream'
STL_MIMETYPE = 'application/vnd.ms-pki.stl'
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

PRISMA_BATCH_SIZE = 1000

ENTRIES_PER_PAGE = 1000
MAX_PAGES = 100
# how many pages to go per folder, set to 1 for testing

NUM_THREADS = 30  # just put the max that works?? don't know what number is maximum for a given architecture, but can find by doubling

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly',
          'https://www.googleapis.com/auth/drive']


# load in the model id to stl and binvox id data
# STL_TO_MODEL_ID = pd.read_csv("data/id_data.csv", index_col=1)
# BINVOX_TO_MODEL_ID = pd.read_csv("data/id_data.csv", index_col=2)

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
    query = f"'{folderId}' in parents"  # needs space!
    if mimeType:
        query += f" and mimeType = '{mimeType}'"
    # query = f"'{FOLDER_ID}' in parents and mimeType = '{binvox_mimeType}'" # binvox
    results = []
    try:
        results = service.files().list(
            pageSize=ENTRIES_PER_PAGE,
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=nextPageToken).execute()
    except HttpError:
        print(f"Error for token {nextPageToken}")
    # print(results)
    return results


def get_all_files_of_type(folderId, service, mimeType, pageLimit=MAX_PAGES):

    direct_files = get_files_directly_in(folderId, service)
    results = [f for f in direct_files.get(
        'files', []) if f['mimeType'] == mimeType]

    i = 1
    while ('nextPageToken' in direct_files and i < pageLimit):
        print(f"Page {i} for {folderId}")
        direct_files = get_files_directly_in(
            folderId, service, nextPageToken=direct_files['nextPageToken'])
        results += [f for f in direct_files.get('files', [])
                    if f['mimeType'] == mimeType]
        i += 1
    return results

# Get rid of anything after the last dot


def strip_after_dot(s):
    return s[:s.rfind(".")]


class SimpleModel:
    def __init__(self, name, folderId, stlId, binvoxId):
        self.name = name
        self.folderId = folderId
        self.stlId = stlId
        self.binvoxId = binvoxId

    def __str__(self):
        return f"SimpleModel(name={self.name}, folderId={self.folderId}, stl_id={self.stlId}, binvoxId={self.binvoxId})"

    def __repr__(self):
        return self.__str__()


# Used for multiprocessing
def get_files_of_type_in_folder_helper(folderId, service, mimeType):
    files = get_all_files_of_type(folderId, service, mimeType)
    name_to_id = {strip_after_dot(f['name']): f['id'] for f in files}
    return name_to_id


def get_simple_models(folder, service) -> List[SimpleModel]:
    folderId = ALL_FILE_FOLDERS[folder]
    direct_files = get_files_directly_in(folderId, service)
    stl_folder = [f for f in direct_files.get(
        'files', []) if f['mimeType'] == FOLDER_MIMETYPE and "rotated" in f['name']][0]
    binvox_folder = [f for f in direct_files.get(
        'files', []) if f['mimeType'] == FOLDER_MIMETYPE and "Binvox" in f['name']][0]

    # create a pool of worker processes
    with Pool(NUM_THREADS) as p:
        print("Starting to get files from folders")
        stl_files_task = p.apply_async(get_files_of_type_in_folder_helper, args=(
            stl_folder['id'], service, STL_MIMETYPE))
        binvox_files_task = p.apply_async(get_files_of_type_in_folder_helper, args=(
            binvox_folder['id'], service, BINVOX_MIMETYPE))

        # get the results from the tasks
        stl_name_to_id = stl_files_task.get()
        binvox_name_to_id = binvox_files_task.get()

    # Create SimpleModel objects for each file
    all_simple_models = []
    for stl_name in stl_name_to_id.keys():
        if stl_name in binvox_name_to_id:
            all_simple_models.append(SimpleModel(
                stl_name, folderId, stl_name_to_id[stl_name], binvox_name_to_id[stl_name]))
        else:
            print(f"Could not find binvox for {stl_name}")
    print("# Models:", len(all_simple_models))

    return all_simple_models


async def add_models_to_db(models: List[SimpleModel]):
    db = Prisma()
    await db.connect()

    # Add models to db
    prisma_models = [{"name": m.name, "folderId": m.folderId,
                      "stlId": m.stlId, "binvoxId": m.binvoxId} for m in models]

    batches = [prisma_models[i:i + PRISMA_BATCH_SIZE]
               for i in range(0, len(prisma_models), PRISMA_BATCH_SIZE)]

    print("Starting batches")
    for i, batch in enumerate(batches):
        print(f"Batch {i + 1} of {len(batches)}")
        await db.model.create_many(data=batch, skip_duplicates=True)

    await db.disconnect()


async def main():
    creds = token_login()

    try:
        service = build('drive', 'v3', credentials=creds)
        for folder in ALL_FILE_FOLDERS.keys():
            print(f"Starting {folder}")
            models = get_simple_models(folder, service)
            print("Adding models to db")
            await add_models_to_db(models)
            print(f"Done with {folder}")

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    asyncio.run(main())
