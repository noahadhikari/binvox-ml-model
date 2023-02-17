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
        self.binvox_list = os.listdir(binvox_dir)
        print(self.binvox_labels)
    
    def __len__(self):
        return len(self.binvox_list)
    
    def __getitem__(self, idx):
        binvox_path = os.path.join(self.binvox_dir, self.binvox_list[idx])
        with open(binvox_path, 'rb') as f:
            binvox_model = binvox_rw.read_as_3d_array(f)
        label = self.binvox_labels.iloc[idx, 1]
        
        return binvox_model.data, label
    
    
if __name__ == "__main__":
    b = BinvoxDataset('data/ratings.json', 'data/binvox')
    
    