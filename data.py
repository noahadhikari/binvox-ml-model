import torch
from torch.utils.data import Dataset

class BinvoxDataset(Dataset):
    def __init__(self, binvox_dir):
        self.binvox_dir = binvox_dir
    
    def __len__(self):
        return len(self.binvox_dir)
    
    def __getitem__(self, idx):
        binvox_path =  