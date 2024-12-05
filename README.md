## Setup

### Cloning the repository

Run `git clone https://github.com/noahadhikari/binvox-ml-model.git` in a Bash-like terminal (e.g. [Git Bash](https://gitforwindows.org/)) to clone this repository to a location of your choosing. Then `cd` into it and open the `binvox-ml-model/` folder in an editor such as VSCode or PyCharm.

### NOTE

**The following commands and scripts should be run from `binvox-ml-model/`** (the parent folder), **not `binvox-ml-model/scripts/`.** If you don't do this, the scripts may not be able to find the `data/` directory and credentials. However, if you're still running into this problem, you can create a copy of the `data/` folder and credentials files inside of `scripts/` as well (but these two folders should be identical!).

### Creating a virtual environment

If you know how to use Anaconda, you can use that instead.

Using a virtual environment before package installation is recommended. Python 3.11.3 must be used for the virtual environment to properly run any code. To set up the environment
1. Make sure you have Python 3.11 installed. Check this by running `python3.11 --version`. If you do not have it installed already, make sure to [install Python 3.11.3](https://www.python.org/downloads/release/python-3113). 
2. Run `python3.11 -m venv ./venv` from the `binvox-ml-model` directory, which should create a folder called `venv`. This will create a virtual environment running Python 3.11.3. 
3. Then, run `source venv/Scripts/activate` if you're using Windows or `source venv/bin/activate` if you're using Mac/Linux. This will activate the virtual environment you just created. If you're using an editor like VSCode or PyCharm, you'll also need to switch the Python interpreter to use the virtual environment you just created.

To get out of the virtual environment, simply run `deactivate`.

### Package installation

Python 3.11.3 was used. Once you're inside the virtual environment, you can install all the dependencies using `pip install -r requirements.txt`.

### Environment variables

In order to get the database url to connect to the database: 
1. Go to the PlanetScale database (labeled-voxels).
2. Go to Connect > Create password > Prisma > Add credentials > Add credentials to .env. Copy the provided code, which should look something like the following
```
DATABASE_URL = 'mysql://example'
```
3. Create a `.env` in the project directory and copy the line from the previous step into the file. This will be the only line in the file.
   
### Activating Prisma

Run `prisma generate` from the `binvox-ml-model` directory. You should see a `prisma/` folder show up. 

### Viewing the database

To view the database in Prisma's GUI, you can run `prisma studio` from the `binvox-ml-model` directory. You should see a GUI pop up in your browser.

## Data Acquisition

### Acquiring ID data

1. Make a folder called `data/` in the `binvox-ml-model/` folder.
2. Run `python scripts/db_id_querier.py`. This will retrieve ID data from the database for STL and binvox models. There should be a file called `id_data.csv` within the `data/` folder now. 

### Acquiring ratings

1. Run `python scripts/db_rating_querier.py`. This will retrieve ratings data from the database for each model. There should be a file called `rating_data.csv` within the `data/` folder now. 

### Acquiring Drive Links

1. Download [this zip file](https://drive.google.com/file/d/1uQdS6GIRAOIrUiY4x7oS68rR7saXCtXU/view?usp=sharing) containing drive links for each part folder.
2. Move it into the `data/` folder and unzip it. You should now have a new folder called `model_links/` within `data/` with the following files:
   - `stl_files.csv`
   - `parents.csv`
   -  `64_res.csv`
   -  `default_res.csv`
TODO here
### Acquiring Google credentials

Follow the steps in the quickstart here and see if you can get `quickstart.py` working: https://developers.google.com/drive/api/quickstart/python


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

If everything is set up correctly, once you have a few models downloaded, you should be able to run `dataset.py` without any errors. You may need to move the `scripts/data/` folder to `data` (in the root directory).

## Machine Learning Model

Once you have some binvox files downloaded, you can try running the ML model. For this example, try `model_for_tweaker_labels.py`. This is an example machine learning model in PyTorch with our dataset - feel free to tweak it as you like. `self.seq` is where the network is handled; modify it to your liking! 
