import torch
import torch.nn as nn
import binvox_rw
import torch.utils.data as data

from dataset import BinvoxDataset

class BinvoxMLModel(nn.Module):
    
    DIM = 256
    def __init__(self):
        super(BinvoxMLModel, self).__init__()
        self.seq = nn.Sequential(
            Conv2Plus1d(1, 16, kernel_size=(5, 4, 4), stride=(1, 2, 2), padding=(1, 0, 0)),
            nn.LayerNorm((16, 256, 64, 64)),
            nn.MaxPool3d(kernel_size=(1, 2, 2)),
            
            Conv2Plus1d(16, 64, kernel_size=(3, 3, 3), padding="same"),
            nn.LayerNorm((64, 256, 32, 32)),
            nn.MaxPool3d(kernel_size=(1, 2, 2)),
            
            nn.Conv3d(64, 256, kernel_size=(3, 3, 3), stride=2),
            nn.MaxPool3d(kernel_size=(1, 2, 2)),
            
            nn.Conv3d(256, 1024, kernel_size=(3, 3, 3), stride=2),
            nn.MaxPool3d(kernel_size=(2, 1, 1)),
            
            nn.Conv3d(1024, 4096, kernel_size=(4, 1, 1)),
            nn.MaxPool3d(kernel_size=(4, 1, 1)),
            
            nn.Conv3d(4096, 4096, kernel_size=(4, 1, 1)),
            nn.ReLU(),
            
            nn.Conv3d(4096, 4096, kernel_size=(4, 1, 1)),
            nn.ReLU(),
            
            nn.Flatten(0),
            nn.Linear(4096, 5),
            nn.Softmax(dim=0)
        )
        
    def forward(self, x):
        x = x.float() # convert voxel boolean array to float
        x = self.seq(x)
        # output is a 1x5 tensor representing the probability of (-2, -1, 0, 1, 2) respectively
        return x.reshape(1, 5)
        
        

class Conv2Plus1d(nn.Module):
    def __init__(self, in_channels, num_filters, kernel_size, stride=1, padding=0):
        #source: https://www.tensorflow.org/tutorials/video/video_classification
        super(Conv2Plus1d, self).__init__()
        self.seq = nn.Sequential(
            # Spatial decomposition
            nn.Conv3d(in_channels, num_filters, kernel_size=(1, kernel_size[1], kernel_size[2]), stride=stride, padding=padding),
            # Temporal decomposition
            nn.Conv3d(num_filters, num_filters, kernel_size=(kernel_size[0], 1, 1), stride=stride, padding=padding),
        )
    
    def forward(self, x):
        return self.seq(x)
    

# source: https://pytorch.org/tutorials/beginner/basics/optimization_tutorial.html
def training_loop(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)
    for batch, (X, y) in enumerate(dataloader):
        pred = model(X)
        loss = loss_fn(pred, y + 2)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        if batch % 1 == 0:
            loss, current = loss.item(), (batch + 1) * len(X)
            print(f"loss: {loss:>7f}  [{current:>5d}/{size:>5d}]")

# source: https://pytorch.org/tutorials/beginner/basics/optimization_tutorial.html
def test_loop(dataloader, model, loss_fn):
    size = len(dataloader.dataset)
    num_batches = len(dataloader)
    print(num_batches)
    test_loss, correct = 0, 0
    
    max_iter = 1

    with torch.no_grad():
        for i, (X, y) in enumerate(dataloader):
            pred = model(X)
            print(i)
            # add 2 because ratings from -2 to 2, convert to 0 to 4
            test_loss += loss_fn(pred, y + 2).item()
            correct += (pred.argmax(1) == y).type(torch.float).sum().item()
            if i > max_iter:
                break

    test_loss /= min(max_iter, num_batches)
    correct /= min(max_iter, num_batches)
    print(f"Test Error: \n Accuracy: {(100*correct):>0.1f}%, Avg loss: {test_loss:>8f} \n")
    


if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using {device} device")
    
    model = BinvoxMLModel().to(device)
    print(model)
    
    
    dataset = BinvoxDataset('data/rating_data.csv', 'data/id_data.csv')
    
    sampler = data.BatchSampler(data.RandomSampler(dataset), batch_size=1, drop_last=False)
    loader = data.DataLoader(dataset, batch_sampler=sampler)
    
    training_loop(loader, model, nn.CrossEntropyLoss(), torch.optim.Adam(model.parameters(), lr=0.001))
    