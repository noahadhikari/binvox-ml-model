import asyncio
from prisma import Prisma
from typing import List

import json

import pandas as pd

class Rating:
    id: int
    modelId: int
    reasoning: str
    userId: str
    score: int
    tweakerScore: float
    model: object
    creator: object
    


async def main() -> None:
    db = Prisma()
    await db.connect()

    # models = await db.model.find_many()

    # async def get_modelId_from_stlID(stlID: str):
    #     return await db.model.find_first(where={'stlId': stlID})

    # model = await get_modelId_from_stlID('1YkElT0POFyn9cVbOr2fNOWt9S_kiUPf6')
    
    async def get_ratings() -> List[Rating]:
        return await db.rating.find_many(take=10000)
    
    offset = 0
    df = pd.DataFrame()
    ratings = await get_ratings()
    with open("data/ratings.json", "w") as f:
        f.write(json.dumps(list(map(lambda r : r.__dict__, ratings)), indent=4))

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
