## Setup

### Cloning the repository

Run `git clone https://github.com/noahadhikari/binvox-ml-model.git` in a Bash-like terminal (e.g. [Git Bash](https://gitforwindows.org/)) to clone this repository to a location of your choosing. Then `cd` into it and open the `binvox-ml-model/` folder in an editor such as VSCode or PyCharm.

### Package installation

Python 3.10.11 and the following packages (and their subdependencies) were used:

- `pandas=2.0.1`
- `prisma=0.8.2`
- `google-api-python-client=2.86.0`
- `google-auth-httplib2=0.1.0`
- `google-auth-oauthlib=1.0.0`
- `tqdm=4.65.0`
- `pytorch=1.12.1`

## Data Acquisition

NOTE: For these acquisition steps, you may need to move the `data` folder inside the `scripts` folder. I'm not sure why because the directory is set to be the root directory.

### Acquiring ID data

Firstly, make a folder called `data/` in the `binvox-ml-model/` folder. Run `scripts/db_id_querier` to get the ID data from the database for STL and binvox models.

### Acquiring ratings

Then, run `scripts/db_rating_querier` to get ratings for models.


### Acquiring Google credentials

Follow the steps in the quickstart here and see if you can get `quickstart.py` working: https://developers.google.com/drive/api/quickstart/python

This will set up the environment expected for `scripts/download_all_models.py`.

NOTE: You may need to do the following steps before Google's `quickstart.py` will work.

Change the port on the line `creds = flow.run_local_server(port=0)` to be `port=8080` instead of `port=0`. Then do the following:

Create an OAuth client ID for Web Application and add the following to its Authorized JavaScript origins (unsure of how many of these are necessary):
- http://localhost
- https://model-rating.vercel.app
- http://localhost:8080

and the following to Authorized redirect URIs:
- http://localhost:3000/api/auth/callback/google
- https://model-rating.vercel.app/api/auth/callback/google
- http://localhost
- http://localhost:8080/


### Environment variables

If you have gotten `quickstart.py` to work, you should have the Google credentials set up in your folder. You will also need to create a `.env` file in the folder with the following lines:

```
GOOGLE_API_KEY = {Google Drive API key here}
DATABASE_URL = '{the database url}'
```

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

