
import pandas as pd
import numpy as np
import os
from tqdm import tqdm


# 6: 1-3500, 3501-7000, 7001-10567
# 7: 1-3667, 3668-7334, 7335-11046
# 8: 1-3500, 3501-7000, 7001-10222

PARTITIONED_FOLDERS = {
    "parts_6_files_1_to_3500_64_resolution": "17Tomwp9gSCGL54tORcxBYTIq08hlVbVJ",
    "parts_6_files_3501_to_7000_64_resolution": "1mpPRuCfFv2A_Xv6e-LFdD1sMKrUt-pjK",
    "parts_6_files_7001_10567_64_resolution": "1F-C_PwR6vsk90cXKVtaY2bOdx_ZLoaKB",
    "parts_7_files_1_to_3667_64_resolution": "1u4y9Mjpg3NM-SI27dr5tMjVUwB6ibiSG",
    "parts_7_files_3668_to_7334_64_resolution": "1mo6_so7q8fX4LmcWiiL3mao_uqMh1j-p",
    "parts_7_files_7335_11046_64_resolution": "1ZA6E3t6ayo5bOMBMVaZgBqbOCh5eLij5",
    "parts_8_files_1_to_3500_64_resolution": "1JInIBDb4icrMGPMk4bladLpNmTiDTW_m",
    "parts_8_files_3501_to_7000_64_resolution": "1M3aFmYbn_msl7VEUV8grx70-5vXM8Q7U",
    "parts_8_files_7001_10222_64_resolution": "1qjyaoedbdDHw5lLoWgyHIl1f91dwFJI0",
    "PARTS_10": "1wUmkgUvyEZ-u_LAcOR9bqSoMU-yWS-dh",
}

PARTITIONED_FOLDERS_REV = {v: k for k, v in PARTITIONED_FOLDERS.items()}

# for each part in folder
# look up part name in db, find associated folder id
# find folder associated with that folder id
# move part to that folder

# make folders for each key in PARTITIONED_FOLDERS_REV
# naming format: parts_x_files_a_to_b_64_resolution

id_data = pd.read_csv("data/id_data.csv")

# sort id_data by column name
id_data.sort_values(by="name", inplace=True)

# get column name
name = id_data["name"]

folder = "(64) parts_8, all files"

# iterate over file names in folder
for file in tqdm(os.listdir(os.path.join("data", folder, "Binvox_files_64_res_compressed"))):
    # remove the file extension and "_compressed" from the file name
    file_name = file.split(".binvox")[0].split("_compressed")[0]

    # find the index of the file name in the name column using searchsorted
    index = name.searchsorted(file_name)

    # check if the name actually exists in the series
    if name.iat[index] != file_name:
        print(f"{file_name} not found in id_data")
        continue

    # get the associated folder id
    folder_id = id_data["folderId"].iat[index]

    # convert the folder id to the associated folder name
    folder_name = os.path.join("data", "partitioned", PARTITIONED_FOLDERS_REV[folder_id])

    # move the file to the associated folder
    os.rename(os.path.join("data", folder, "Binvox_files_64_res_compressed", file), os.path.join(folder_name, file))