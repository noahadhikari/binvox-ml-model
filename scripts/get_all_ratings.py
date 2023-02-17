import requests
import json
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


if __name__ == "__main__":
    # write the ratings to a file called ratings.json
    with open("data/ratings.json", "w") as f:
        # pretty print the json
        f.write(json.dumps(getRatings(), indent=4))