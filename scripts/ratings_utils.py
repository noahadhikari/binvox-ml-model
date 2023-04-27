import asyncio
from prisma import Prisma
from add_models_to_db import ALL_FILE_FOLDERS
from collections import defaultdict
from add_models_to_db import strip_after_dot, PRISMA_BATCH_SIZE

PRISMA_MAX_QUERY_SIZE = 99999


async def get_all_ratings():
    prisma = Prisma()
    await prisma.connect()

    all_ratings = []
    # Get all ratings in batches
    skip = 0
    while True:
        ratings = await prisma.rating.find_many(skip=skip, take=PRISMA_MAX_QUERY_SIZE)
        if len(ratings) == 0:
            break
        all_ratings.extend(ratings)
        skip += PRISMA_MAX_QUERY_SIZE

    await prisma.disconnect()
    return all_ratings


async def verify_all_models_are_unique():
    prisma = Prisma()
    await prisma.connect()

    # Get models with the same STL_ID
    for folder in ALL_FILE_FOLDERS.keys():
        folder_id = ALL_FILE_FOLDERS[folder]
        print("Folder:", folder_id)
        models = await prisma.model.find_many(where={'folderId': folder_id})
        # Check to see if any of the models have the same stlId
        stl_id_set = {model.stlId for model in models}
        print(len(stl_id_set), len(models))

    await prisma.disconnect()

# Note: We can have multiple ratings for the same model, but only one with a tweaker score


async def remove_duplicate_tweaker_ratings():
    prisma = Prisma()
    await prisma.connect()

    all_ratings = await get_all_ratings()
    print("Total ratings:", len(all_ratings))

    model_id_to_ratings = defaultdict(list)
    for rating in all_ratings:
        model_id_to_ratings[rating.modelId].append(rating)
    all_dupliclate_ratings = []
    for _, ratings in model_id_to_ratings.items():
        # if len(ratings) > 1:
        # 	print("Model", model_id, "has", len(ratings), "ratings:", ratings)
        tweaker_scores = [
            rating for rating in ratings if rating.tweakerScore is not None]
        if len(tweaker_scores) > 1:
            # Add all but the first tweaker score
            all_dupliclate_ratings.extend(tweaker_scores[1:])

    print("Total duplicate ratings:", len(all_dupliclate_ratings))
    # Delete all duplicate ratings
    if len(all_dupliclate_ratings) > 0:
        await prisma.rating.delete_many(
            where={'id': {'in': [rating.id for rating in all_dupliclate_ratings]}})

    await prisma.disconnect()


async def remove_duplicate_manual_ratings():
    """
    2 manual ratings are duplicates if they have the same modelId, score, and reasoning.
    Tweakerscore must be None
    """
    prisma = Prisma()
    await prisma.connect()

    all_ratings = await get_all_ratings()

    manual_ratings = [r for r in all_ratings if r.tweakerScore is None]
    print("Total manual ratings:", len(manual_ratings))

    # Create a dictionary that represent the unique rating to all ratings with that unique rating
    unique_ratings = defaultdict(list)
    for rating in manual_ratings:
        unique_ratings[(rating.modelId, rating.score,
                        rating.reasoning)].append(rating)
    print("Total unique ratings:", len(unique_ratings))

    # Find the duplicate ratings
    duplicate_ratings = []
    for _, ratings in unique_ratings.items():
        duplicate_ratings.extend(ratings[1:])

    print(len(duplicate_ratings))
    # Delete all duplicate ratings
    if len(duplicate_ratings) > 0:
        await prisma.rating.delete_many(where={'id': {'in': [rating.id for rating in duplicate_ratings]}})

    print(f"Deleted {len(duplicate_ratings)} duplicate ratings")
    await prisma.disconnect()


class TweakerRating:
    def __init__(self, modelId, tweakerScore):
        self.modelId = modelId
        self.reasoning = "Tweaker"
        self.userId = "clddy85gg00003ypcqx4r08wl"
        self.tweakerScore = tweakerScore

    def __str__(self):
        return f"TweakerRating(modelId={self.modelId}, tweakerScore={self.tweakerScore})"
    __repr__ = __str__


async def add_tweaker_scores_to_db(filepath):
    """
        Reads in the tweaker scores from the csv file and adds them to the database.
        Each line in the CSV file should be of the form:
        <MODEL_NAME>,<SCORE>, ie: 00007eb3-6ed3-45a9-8a41-990953ca0284.stl,6.602921662456482
    """
    # Maps model name to tweaker score
    model_name_to_score = {}
    print('Getting tweaker scores from', filepath)
    with open(filepath, 'r') as f:
        for line in f:
            model_name, score = line.split(',')
            # Remove the .stl from the model name
            model_name = strip_after_dot(model_name)
            model_name_to_score[model_name] = float(score)
    print("Total ratings:", len(model_name_to_score))

    prisma = Prisma()
    await prisma.connect()

    model_names = set(model_name_to_score.keys())

    # Find the models that have the same name as the tweaker scores
    models = await prisma.model.find_many(where={'name': {'in': model_names}})

    # Maps model name to TweakerRating
    model_name_to_tweaker_rating = {}
    for model in models:
        model_name_to_tweaker_rating[model.name] = TweakerRating(
            model.id, model_name_to_score[model.name])

    prisma_ratings = [{"modelId": rating.modelId, "reasoning": rating.reasoning, "userId": rating.userId,
                       "tweakerScore": rating.tweakerScore} for rating in model_name_to_tweaker_rating.values()]
    batches = [prisma_ratings[i:i + PRISMA_BATCH_SIZE]
               for i in range(0, len(prisma_ratings), PRISMA_BATCH_SIZE)]
    print("Starting batches")

    for i, batch in enumerate(batches):
        print(f"Batch {i + 1} of {len(batches)}")
        await prisma.rating.create_many(data=batch, skip_duplicates=True)

    print(
        f"Added {len(model_name_to_tweaker_rating)} tweaker ratings for {filepath}")

    await prisma.disconnect()


async def main():
    # filepaths = [
    #     "tweaker_scores/parts8_1-3500.csv",
    #     "tweaker_scores/parts8_3501-7000.csv",
    #     "tweaker_scores/parts8_7001-10222.csv",
    #     "tweaker_scores/parts10.csv",
    # ]
    # for filepath in filepaths:
    #     await add_tweaker_scores_to_db(filepath)
    # await remove_duplicate_tweaker_ratings()
    all_ratings = await get_all_ratings()
    print(len(all_ratings))

if __name__ == '__main__':
    asyncio.run(main())
