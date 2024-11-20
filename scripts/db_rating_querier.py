import os
from pathlib import Path
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
    

script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute paths
data_dir = os.path.join(script_dir, "../data")

async def main() -> None:
    db = Prisma()
    await db.connect()

    # models = await db.model.find_many()

    # async def get_modelId_from_stlID(stlID: str):
    #     return await db.model.find_first(where={'stlId': stlID})

    # model = await get_modelId_from_stlID('1YkElT0POFyn9cVbOr2fNOWt9S_kiUPf6')
    
    # async def get_ratings() -> List[Rating]:
    #     return await db.rating.find_many(take=10000)
    
    # offset = 0
    # df = pd.DataFrame()
    # ratings = await get_ratings()
    # with open("data/ratings.json", "w") as f:
    #     f.write(json.dumps(list(map(lambda r : r.__dict__, ratings)), indent=4))

    # await db.disconnect()

    async def get_ratings(offset: int = 0, limit: int = 100000):
        # return await db.model.find_many(select={'id': True, 'stlId': True, 'binvoxId': True}, take=100)
        return await db.query_raw(f'SELECT * \
                                    FROM Rating \
                                    ORDER BY id ASC \
                                    LIMIT {limit} \
                                    OFFSET {offset}')
    
    offset = 0
    df = pd.DataFrame()
    id_data = await get_ratings(offset)
    
    while (id_data):
        df = pd.concat([df, pd.DataFrame(id_data)], ignore_index=True)
        
        offset += 100000
        id_data = await get_ratings(offset)
    
    # write the resulting dataframe to a csv file
    with open(os.path.join(data_dir, "rating_data.csv"), 'w', newline='') as f:
        df.to_csv(f, index=False, header=True)

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
