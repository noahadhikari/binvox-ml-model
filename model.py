import torch
import torch.nn as nn
import binvox_rw
from torch.utils.data import DataLoader

class BinvoxRCNN(nn.Module):
    def __init__(self):
        super(BinvoxRCNN, self).__init__()
        
        # Recurrent Convolutional Neural Network with each 2D layer representing how the 3D model evolves over time
        
        self.CNN_stack = nn.Sequential(
            
        )
    


