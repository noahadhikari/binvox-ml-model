## Setup

### Cloning the repository

Run `git clone https://github.com/noahadhikari/binvox-ml-model.git` in a Bash-like terminal (e.g. [Git Bash](https://gitforwindows.org/)) to clone this repository to a location of your choosing. Then `cd` into it and open the `binvox-ml-model/` folder in an editor such as VSCode or PyCharm.

### NOTE

**The following commands and scripts should be run from `binvox-ml-model/`** (the parent folder), **not `binvox-ml-model/scripts/`.** If you don't do this, the scripts may not be able to find the `data/` directory and credentials. However, if you're still running into this problem, you can create a copy of the `data/` folder and credentials files inside of `scripts/` as well (but these two folders should be identical!).

### Creating a virtual environment

If you know how to use Anaconda, you can use that instead.

Using a virtual environment before package installation is recommended. To do so, run `python -m venv ./venv` from the `binvox-ml-model` directory, which should create a folder called `venv`. Then, run `source venv/Scripts/activate` to activate the virtual environment. If you're using an editor like VSCode or PyCharm, you'll also need to switch the Python interpreter to use the virtual environment you just created.

To get out of the virtual environment, simply run `deactivate`.

### Package installation

Python 3.11.3 was used. Once you're inside the virtual environment, you can install all the dependencies using `pip install -r requirements.txt`.

### Environment variables

You will need to create a `.env` file in the folder with the following lines (omitting the curly braces):

```
GOOGLE_API_KEY = {Your Google Drive API key here. You can omit this for now and fill it in later}
DATABASE_URL = 'mysql://8v16gwff0ymgk9l6w7ya:pscale_pw_fXIQMOV0GDVYKTlboglsGEdOy1wXGack6URd7oCtPPZ@aws.connect.psdb.cloud/labeled-voxels?sslaccept=strict'
```

### Activating Prisma

Run `prisma generate` from the `binvox-ml-model` directory. You should see a `prisma/` folder show up. You may need to copy it into the `scripts/` folder if the following steps aren't working.

### Viewing the database

To view the database in Prisma's GUI, you can run `prisma studio` from the `binvox-ml-model` directory. You should see a GUI pop up in your browser.

## Data Acquisition

NOTE: For these acquisition steps, you may need to move the `data` folder inside the `scripts` folder. I'm not sure why because the directory is set to be the root directory.

### Acquiring ID data

Firstly, make a folder called `data/` in the `binvox-ml-model/` folder. Run `scripts/db_id_querier.py` to get the ID data from the database for STL and binvox models.

### Acquiring ratings

Then, run `scripts/db_rating_querier.py` to get ratings for models.


### Acquiring Google credentials

Follow the steps in the quickstart here and see if you can get `quickstart.py` working: https://developers.google.com/drive/api/quickstart/python

At this point, you can go back to `.env` and fill in the remaining line for `GOOGLE_API_KEY`.

This will set up the environment expected for `scripts/download_all_models.py`.

NOTE: You may need to do the following steps before Google's `quickstart.py` will work:

Create an OAuth client ID for Web Application and add the following to its Authorized JavaScript origins (unsure of how many of these are necessary):
- http://localhost
- https://model-rating.vercel.app
- http://localhost:8080

and the following to Authorized redirect URIs:
- http://localhost:3000/api/auth/callback/google
- https://model-rating.vercel.app/api/auth/callback/google
- http://localhost
- http://localhost:8080/

### Modifying scopes

After successfully running `quickstart.py`, delete `token.json` and you should be able to run `download_all_models.py`. This will update the token to have download access (the quickstart only allows read access).

`download_all_models.py` has `ALL_FILE_FOLDERS`, which designates the folders to download from Google Drive. It assumes the binvox folder for a specific parts folder contains the string "Binvox" and the stl folder contains the string "rotated".

### Acquiring 3D models

Once you have `ratings.json` and `id_data.csv` set up, you should be able to run `download_all_models.py`. This script will download the STL and Binvox files from Google Drive.

A few things of note:

- `ALL_FILE_FOLDERS` refers to the Google Drive folder IDs of whichever folders you would like to download.
- For each Drive folder, it assumes the Binvox files are stored in a folder containing the string "Binvox" and the STL files are stored in a folder containing the string "rotated".
- `ENTRIES_PER_PAGE` refers to the batch size when querying Google Drive's API. It has a maximum of `1000`, and I recommend `1000` (it's not significantly faster to only have a batch size of `1`).
- `MAX_PAGES` refers to how many pages we go per folder before moving on to the downloading step. For testing purposes, I suggest setting this to `1`, When actually running the script, I suggest setting this to around `100` (each folder contains tens of thousands of models).
- `NUM_THREADS` refers to how many threads we use when downloading the files. The higher, the faster the script will run. You can find a good point by doubling the number until it gets too big for your computer, then middling the results (similar to binary search). Note that using a lot of threads will significantly slow your computer's performance while running the script.
- The amount of data is **enormous**. We have around 600k ratings, and each one corresponds to a Binvox and STL model of varying file size. With an estimate of 100KB each, we're getting close to hundreds of gigabytes! Be wary of this if you're trying to download all of the data at once.
- **Running this script will likely slow your computer to a crawl**, especially if you're using a lot of threads. Use caution if you are doing important tasks in the background.

## Testing

If everything is set up correctly, you should be able to run `dataset.py` without any errors.

## Machine Learning Model

Once you have some binvox files downloaded, you can try running the ML model. For this example, try `model_for_tweaker_labels.py`.

If that looks to be training, you're good to go!

