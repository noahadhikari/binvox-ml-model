import asyncio
from prisma import Prisma

import json

import pandas as pd

# script used to update folderIds to folderNames when changing schema
async def main() -> None:
    db = Prisma()
    await db.connect()

    # read spreadsheet csv w/ folderName: folderId mappings
    parents = pd.read_csv("data/parents.csv")
    # iterate through folderName, folderId
    for _, row in parents.iterrows():
        folderId = row['folderId']
        folderName = row['folderName']
        # update all instances of folderId in prismadatabase
        amount_updated = await db.model.update_many(
            where={
                'folderId': folderId
            },
            data={
                'folderName': folderName
            }
        )

        print(f"{amount_updated} records were updated with {folderName}")

    print("db updated!")

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())

    