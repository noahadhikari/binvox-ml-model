import binvox_rw
import os
import csv

import pandas as pd
import numpy as np

import torch
from torch.utils.data import Dataset


class BinvoxDataset(Dataset):

    BINVOX_DATA_DIR = "data/binvox"

    def __init__(self, ratings_csv, id_data_csv):
        raw_ratings = pd.read_csv(ratings_csv)
        id_data = pd.read_csv(id_data_csv, sep=",", header=0)
        
        #rename the id column of id_data to modelId
        id_data = id_data.rename(columns={"id": "modelId"})

        # add the binvoxId and stlId to the ratings data
        self.binvox_labels = pd.merge(raw_ratings, id_data, on="modelId")

        # if binvox id is None then drop that row
        self.binvox_labels = self.binvox_labels.dropna(subset=['binvoxId'])
        
        # NOTE: using tweaker scores for now. if tweaker score is None then drop that row.
        # If you want to use manual scores, change the column name to "score"
        self.binvox_labels = self.binvox_labels.dropna(subset=['tweakerScore'])

        # conjoin the id to the folderId to get the full path
        self.binvox_labels["full_binvox_path"] = \
            self.BINVOX_DATA_DIR + "/" + \
            self.binvox_labels['folderId'] + "/" + \
            self.binvox_labels['modelId'].astype(str) + ".binvox"

        self.binvox_labels = self.binvox_labels[self.binvox_labels["full_binvox_path"].apply(lambda x : os.path.exists(x))]
        

    def __len__(self):
        return len(self.binvox_labels)

    def __getitem__(self, idx):
        full_path = self.binvox_labels.iloc[idx]["full_binvox_path"]
        # print(full_path)
        with open(full_path, 'rb') as f:
            binvox_model = binvox_rw.read_as_3d_array(f)
        score = self.binvox_labels.iloc[idx]["tweakerScore"]

        return binvox_model.data, score


if __name__ == "__main__":
    b = BinvoxDataset('data/ratings.csv', 'data/id_data.csv')
    print(b[0])
