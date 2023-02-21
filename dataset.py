import binvox_rw
import os
import csv

import pandas as pd
import numpy as np

import torch
from torch.utils.data import Dataset

class BinvoxDataset(Dataset):
    
    BINVOX_DATA_DIR = "data/binvox"
    
    def __init__(self, ratings_json):
        self.binvox_labels = pd.read_json(ratings_json)
        # if binvox id is None then drop that row
        self.binvox_labels = self.binvox_labels.dropna(subset=['binVoxId'])
        #conjoin the modelId to the folderId to get the full path
        self.binvox_labels["full_binvox_path"] = self.BINVOX_DATA_DIR + "/" + self.binvox_labels['folderId'] + "/" + self.binvox_labels['modelId'].astype(str) + ".binvox"
        for file in self.binvox_labels["full_binvox_path"]:
            if not os.path.exists(file):
                # print(f"File {file} does not exist")
                self.binvox_labels = self.binvox_labels.drop(self.binvox_labels[self.binvox_labels["full_binvox_path"] == file].index)
        # print(self.binvox_labels)
        
    def __len__(self):
        return len(self.binvox_labels)
    
    def __getitem__(self, idx):
        full_path = self.binvox_labels.iloc[idx]["full_binvox_path"]
        # print(full_path)
        with open(full_path, 'rb') as f:
            binvox_model = binvox_rw.read_as_3d_array(f)
        score = self.binvox_labels.iloc[idx]["score"]
        
        return binvox_model.data, score
    
    
if __name__ == "__main__":
    b = BinvoxDataset('data/ratings.json')
    # print(b[0])
    