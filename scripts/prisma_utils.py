import asyncio
from prisma import Prisma
import pandas as pd

PRISMA_MAX_QUERY_SIZE = 99999

async def get_all_rows_in_table(table) -> list:
    all_rows = []
    # Get all models in batches
    skip = 0
    while skip < 1:
        print(f"Getting rows {skip} to {skip + PRISMA_MAX_QUERY_SIZE}")
        rows = await table.find_many(skip=skip, take=PRISMA_MAX_QUERY_SIZE)
        if len(rows) == 0:
            break
        all_rows.extend(rows)
        skip += PRISMA_MAX_QUERY_SIZE
    return all_rows

def convert_list_to_df(list) -> pd.DataFrame:
    print(dir(list[0]))
    return pd.DataFrame(list, columns=list[0].keys())

async def main():
    prisma = Prisma()
    await prisma.connect()
    print(prisma.model)
    print(convert_list_to_df(await get_all_rows_in_table(prisma.model)))
    await prisma.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

