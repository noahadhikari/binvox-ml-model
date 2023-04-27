import asyncio
from prisma import Prisma

import json

import pandas as pd


async def main() -> None:
    db = Prisma()
    await db.connect()

    # models = await db.model.find_many()

    # async def get_modelId_from_stlID(stlID: str):
    #     return await db.model.find_first(where={'stlId': stlID})

    # model = await get_modelId_from_stlID('1YkElT0POFyn9cVbOr2fNOWt9S_kiUPf6')
    
    async def get_map_from_modelId(offset: int = 0, limit: int = 100000):
        # return await db.model.find_many(select={'id': True, 'stlId': True, 'binvoxId': True}, take=100)
        return await db.query_raw(f'SELECT id, stlId, binvoxId, folderId \
                                    FROM Model \
                                    ORDER BY id ASC \
                                    LIMIT {limit} \
                                    OFFSET {offset}')
    
    offset = 0
    df = pd.DataFrame()
    id_data = await get_map_from_modelId(offset)
    
    while (id_data):
        df = pd.concat([df, pd.DataFrame(id_data)], ignore_index=True)
        
        offset += 100000
        id_data = await get_map_from_modelId(offset)
    
    # write the resulting dataframe to a csv file
    with open('data/id_data.csv', 'w', newline='') as f:
        df.to_csv(f, index=False, header=True)

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

    