import requests
import json
import os
from typing import List, Dict


class Rating:
    id: int
    score: int
    reasoning: str
    modelId: int
    userId: int
    modelName: str
    stlId: int
    binVoxId: int


URL = "https://model-rating.vercel.app/api/trpc/rating.getAllRatings?batch=1&input={%220%22%3A{%22json%22%3Anull%2C%22meta%22%3A{%22values%22%3A[%22undefined%22]}}}"


def getRatings() -> List[Rating]:
    response = requests.get(URL)
    data = json.loads(response.text)
    items = data[0]['result']['data']['json']

    return items

def download_binvox_from_rating(rating):
    """ Given a rating, download its binvox file from Google Drive.
        Only downloads if the binvoxId is not None.
    """
    
    BASE_URL = "https://www.googleapis.com/drive/v3/files/"
    API_KEY = "AIzaSyCRilG62Ju2DZp02N4op5QnOBtEz_F2w5g"
    
    if rating['binVoxId'] is None:
        return
    
    url = f"{BASE_URL}{rating['binVoxId']}?alt=media&key={API_KEY}"
    
    download_and_rename(url, f"data/binvox/{rating['folderId']}", f"{rating['modelId']}.binvox")

def download_stl_from_rating(rating):
    BASE_URL = "https://www.googleapis.com/drive/v3/files/"
    API_KEY = "AIzaSyCRilG62Ju2DZp02N4op5QnOBtEz_F2w5g"
    
    if rating['stlId'] is None:
        return
    
    url = f"{BASE_URL}{rating['stlId']}?alt=media&key={API_KEY}"
    
    download_and_rename(url, f"data/stl/{rating['folderId']}", f"{rating['modelId']}.stl")

def download_and_rename(url, root_dir, filename):
    if (not os.path.exists(root_dir)):
        os.makedirs(root_dir)
        
    r = requests.get(url, allow_redirects=True)
    with open(os.path.join(root_dir, filename), 'wb') as f:
        f.write(r.content)
    
if __name__ == "__main__":
    ratings = getRatings()
    for rating in ratings:
        download_binvox_from_rating(rating)
        download_stl_from_rating(rating)
    with open("data/ratings.json", "w") as f:
        f.write(json.dumps(ratings, indent=4))
    