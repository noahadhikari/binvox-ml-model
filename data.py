import binvox_rw
import os
import csv

import pandas as pd

import torch
from torch.utils.data import Dataset

class BinvoxDataset(Dataset):
    def __init__(self, ratings_json, binvox_dir):
        self.binvox_labels = pd.read_json(ratings_json)
        self.binvox_dir = binvox_dir
        self.binvox_labels["binvox_path"] = self.binvox_labels["modelId"].apply(lambda x: os.path.join(binvox_dir, f"{x}.binvox"))
            
    
    def __len__(self):
        return len(self.binvox_list)
    
    def __getitem__(self, idx):
        binvox_path = self.binvox_labels.iloc[idx]["binvox_path"]
        print(binvox_path)
        with open(binvox_path, 'rb') as f:
            binvox_model = binvox_rw.read_as_3d_array(f)
        score = self.binvox_labels.iloc[idx]["score"]
        
        return binvox_model.data, score
    
    
if __name__ == "__main__":
    b = BinvoxDataset('data/ratings.json', 'data/binvox')
    print(b[224])
    