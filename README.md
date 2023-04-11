# mTBI-EEG

Pipeline for the processing and analysis of EEG data from mild Traumatic Brain Injury patients.
The preprocessing and analysis sections are run separately from different folders.

## Folder structure
The folder structure for the project is shown below. The root folder is `mtbi_eeg`. The code is under `src`. Common scripts and config files are under `src/`.
The modules for data processing and data analysis are under `src/processing/` and `src/analyisis/`.

```
mtbi_meeg/
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── setup.py
├── src/
│   ├── config_eeg.py
│   ├── config_common.py
│   ├── fnames.py
│   ├── README.md
│   ├── system_check.py
│   ├── analysis/
│   │    ├── 01_read_processed_data.py
│   │    ├── 02_plot_processed_data.py
│   │    ├── 03_fit_model_and_plot.py
│   │    ├── 04_create_report.py
│   │    ├── 05_convert_reports_to_pdf.py
│   │    ├── README.md
│   │    └── run_files.py
│   └── processing/
│       ├── 01_freqfilt.py
│       ├── 02_ica.py
│       ├── 03_psds.py
│       ├── 04_bandpower.py
│       ├── run_files.py
│       └── README.md
└── tests/
    ├── test_01_read_processed_data.py
    ├── test_02_plot_processed_data.py
    ├── test_03_fit_model_and_plot.py (WIP)
    ├── test_04_create_report.py (WIP)
    └── test_05_convert_reports_to_pdf.py (WIP)
```

## Getting started

Before the first time you execute the scripts in this repository, you must edit the file `src/config_common.py` and include a new block with information about your user, workstation, data directories, and matplotlib backend:

1. Go to folder `src` and open the file `config_common.py` for editing. From terminal,
    ```
    $ cd src
    $ nano config_common.py
    # You can also use other editors. For VS Code, type `code config_common.py`
    ```
2. Edit the file: add your `user` and `host` to the list. There's a commented block you can use as example [here](https://version.aalto.fi/gitlab/heikkiv7/mtbi-eeg/-/blob/main/python/processing/config_common.py#L78). Copy the block and edit it.
3. Add the path where `raw_data_dir` is expected ('/net/theta/fishpool/projects/tbi_meg/BIDS' in BioMag)
4. Add the path where `processed_data_dir` is expected ('/net/theta/fishpool/projects/tbi_meg/k22_processed' in BioMag)
5. Add the paths where figures and reports will be created into (you can use the directories in this repository or other)
6. Add the matplotlib backend (TBC)
7. Check that your system has the required dependencies by running the script `check_system.py`. From terminal, 

    (_Note: this step will not be needed when installing the package is working ok, but I will leave the instructions until that is clear_)
    ```
    $ python3 check_system.py
    ```
If there's no problems, you should see a message saying that 'System requirements are ok' and you should be ok to run the pipeline now.

#### Version Conflict errors
If there is an issue with packages or versions, you will see a message indicating the library with a Version Conflict. Please update the package
```
# For updating using pip,
$ python3 -m pip upgrade <package-name>
# For updating using conda,
$ conda update <package-name>
```
#### Missing folder errors
 If folders are missing, please create them. These scripts will not create folders automatically.

# Running the pipelines
## Preprocessing

The preprocessing pipeline can be found in `src/processing/`. The aim of this pipeline is to clean up the data and extract useful features, so data can be used by the classifiers in the analysis section.

The list of files is described below:
- `00_maxfilter.py`: applies max filtering (not applicable to this data)
- `01_freqfilt.py`: applies frequency filtering
- `02_ica.py`: removes ocular & heartbeat artefacts with independent component analysis
- `03_psds.py`: computes the PSDs over all channels and saves them as h5 files
- `04_bandpower.py`: calculates band power for each subject and creates a spatial frequency matrix that is then vectorized for later analysis.

**Inputs:**
- a
- b

**Outputs:**
- c 
- d 

To run the pipeline, go to `src/processing/` and do,
```
$ cd src/processing/
# Note: Make sure that subjects.txt exists here
$ python3 run_files.py
```


## Analysis pipeline

The data analysis is done using the scripts in the folder `src/analysis`. The aim is to use different classifiers (LR, LDA, SVM and RF) to differentiate between patients and controls. 

The list of files is described below:
- `01_read_processed_data.py`: Reads in EEG bandpower data from CSV files into a dataframe. The dataframe and the arguments used to run the script are added to a pickle object.
- `02_plot_processed_data.py`: (optional step) Plots the processed EEG data of the PSD intensity for visual assessment.
- `03_fit_model_and_plot.py`: Fits ML classifiers using the processed data, performs cross validation and evaluates the performance of the classification using ROC curves. Outputs a CSV file with the classification results, plots and saves plots to disk and adds the information to a metadata file.
- `04_create_report.py`: (optional) Creates an HTML report with the figures created in step 03.
- `05_convert_report_to_pdf.py`: (optional) Bundle up all htmls into one with a certain cover and create a PDF from it.
- `run_files.py`:

**Inputs:**
- subjects.txt
- processed data (in folder `processed_data_dir`)

**Outputs:**
- CSV file with results from ML classification accuracy metrics
- PNG figure
- HTML report 
- PDF with all the HTML reports

## Things that are yet to be implemented:

- [x] config file for analysis? 
- [x] model fitting
- [ ] hyperparameter optimization, triton-compatible
- [x] model validation
- [x] visualizations
- [x] statistics


## Git stuff

You can ```git clone``` the repo using HTTPS address.
-  [Create](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#create-a-file) or [upload](https://docs.gitlab.com/ee/user/project/repository/web_editor.html#upload-a-file) files
-  [Add files using the command line](https://docs.gitlab.com/ee/gitlab-basics/add-file.html#add-a-file-using-the-command-line) or push an existing Git repository with the following command:

```
cd ~/mtbi-eeg
git pull origin main #maybe...
git branch <your branch name>
git push
```
It is **strongly recommended** to work on separate branches which are later merged to main by the owner of the repo.  
Merge requests are handled together! Check the branch you are currently on by typing ```git status```. 
You can change the branch you are one with the command ```git checkout <your branch name>```.
After pushing, create a merge request and assign someone to go through your code.

>NOTE: Before creating a new branch, ALWAYS pull the main branch from the remote repository!


## Collaboration

-  [Create a new merge request](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
-  [Automatically close issues from merge requests](https://docs.gitlab.com/ee/user/project/issues/managing_issues.html#closing-issues-automatically)
-  [Enable merge request approvals](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/)


## License
Project under MIT License
