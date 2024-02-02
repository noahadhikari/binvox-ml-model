import shutil
import os
import tqdm


def main():
    # Make a folder for holding the compressed data
    os.makedirs("compressed/stl", exist_ok=True)
    # Compress each folder
    for folder in os.listdir("data/stl"):
        # if already exists in the destination folder, skip
        if os.path.exists(f"compressed/stl/{folder}.zip"):
            continue
        print(f"Compressing {folder}")
        shutil.make_archive(f"compressed/stl/{folder}", "zip", f"data/stl/{folder}")


if __name__ == "__main__":
    main()