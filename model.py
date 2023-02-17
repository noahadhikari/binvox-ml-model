import torch
import torch.nn as nn
import binvox_rw
from torch.utils.data import DataLoader

from data import BinvoxDataset

class BinvoxMLModel(nn.Module):
    def __init__(self, dim):
        self.dim = dim
        super(BinvoxMLModel, self).__init__()
        self.seq = nn.Sequential(
            Conv2Plus1d(1, 3, 1, "same"),
        )
        
    def forward(self, x):
        return self.seq(x)
        
        

class Conv2Plus1d(nn.Module):
    def __init__(self, filters, kernel_size, stride=1, padding=0):
        #source: https://www.tensorflow.org/tutorials/video/video_classification
        super(Conv2Plus1d, self).__init__()
        self.seq = nn.Sequential(
            # Spatial decomposition
            nn.Conv3d(1, filters, kernel_size, stride, padding),
            nn.LayerNorm([filters, 1, 1]),
            nn.ReLU(),
            # Temporal decomposition
            nn.Conv3d(1, filters, kernel_size, stride, padding),
            nn.LayerNorm([filters, 1, 1]),
        )
    
    def forward(self, x):
        return self.seq(x)
    

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using {device} device")
    
    model = BinvoxMLModel().to(device)
    print(model)
    
    # dataloader = DataLoader(BinvoxDataset('data/ratings.json', 'data/binvox'), batch_size=1, shuffle=True)
    
    dataset = BinvoxDataset('data/ratings.json', 'data/binvox')
    data_pt = dataset[224]
    
    print(model.forward(data_pt))
    
    