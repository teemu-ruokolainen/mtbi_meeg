#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 10:21:38 2022

@author: aino

Reads bandpower data from csv files and creates a matrix whose rows represent each subject. 
"""
import re
import numpy as np
import csv
import pandas as pd
import argparse
import os
import sys
import pickle
import time

# Get the parent directory of the current file 
processing_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(processing_dir)
from config_common import processed_data_dir
from config_eeg import wide_bands

# TODO: Move method 'define_subtask()' to config_eeg
# TODO: Where to define 'subjects_to_exclude'?

def define_subtasks(task):
    """
    Define the subtasks to be used for the analysis
    
    
    Input parameters
    ---------
    - task: chosen task (eyes open, eyes closed, Paced Auditory Serial Addition Test 1 or PASAT 2)
    
    Returns
    -------
    - chosen_tasks: The list of chosen subtasks
    """
    tasks = [['ec_1', 'ec_2', 'ec_3'], 
             ['eo_1', 'eo_2', 'eo_3'], 
             ['PASAT_run1_1', 'PASAT_run1_2'], 
             ['PASAT_run2_1', 'PASAT_run2_2']]
       
    # Define which files to read for each subject
    if task == 'ec':
        chosen_tasks = tasks[0]
    elif task == 'eo':
        chosen_tasks = tasks[1]
    elif task == 'PASAT_1':
        chosen_tasks = tasks[2]
    elif task == 'PASAT_2': 
        chosen_tasks = tasks[3]
    else:
        raise("Incorrect task")
       
    return chosen_tasks

def read_subjects():
   
    """
    Read in the list of subjects from file subjects.txt. Asserts format to contain two digits and then a letter P or C  
    

    Parameters
    ----------
    
    Returns
    -------
    - subjects: a list with all the subjects
 
    """
     # List of extra controls, dismissed so we'd have equal number of P vs C.
    to_exclude = ['32C', '33C', '34C', '35C', '36C', '37C', '38C', '39C', '40C', '41C', '12P']

    # Get the list of subjects and check the format   
    subject_pattern = r'^\d{2}[PC]'   
    try:
        with open('subjects.txt', 'r') as subjects_file:
            subjects = [line.rstrip() for line in subjects_file.readlines()]
            # Assert that each line has the expected format
            for line in subjects:
                assert re.match(subject_pattern, line), f"Subject '{line}' does not have the expected format."
    except FileNotFoundError as e:
        # File expected in same directory 
        print("The file 'subjects.txt' does not exist in the current directory. The program will exit.")
        raise e
    
    # Excluse subjects with errors
    for i in to_exclude:
        subjects.remove(i)
    
    return subjects

def create_subjects_and_tasks(chosen_tasks, subjects):

    """
    Combines the subjects and with the chosen tasks and creates a list of subjects_and_tasks
    

    Parameters
    ----------
    - chosen_tasks: list of subtaks pertaining to each task 
    - subjects: list of all the subjects
    
    Returns
    -------
    - subjects_and_tasks: a list with 2-uples formed by all the combinations of (subjects, tasks)

    """
   
    # Define a list with 2-uples formed by all the combinations of (subjects, tasks)
    subjects_and_tasks = [(x,y) for x in subjects for y in chosen_tasks]

    print(f'INFO: There are {len(subjects_and_tasks)} subject_and_task combinations.')
    
    return subjects_and_tasks


def read_data(subjects_and_tasks, freq_bands_type, normalization, processed_data_dir):

    """
    Read in processed bandpower data for each subject_and_tasks from files
    Creates an arrays    
    
    Input parameters
    ----------------
    - subjects_and_tasks: list of 2-uples
            Contains the combinations of subjects and segments (e.g., (Subject1, Task1_segment1), (Subject1, Task1_segment2), ...)
    - freq_bands_type: str
            Frequency bins, 'thin' or 'wide'
    - normalization: boolean
            If True, normalization of the PSD data for all channels will be performed   
    - processed_data_dir: str
            path to the processed data directory as defined in config_common
    Output
   -----
    - all_bands_vector: list of np arrays
            Each row contains the PSD data (for the chosen frquency bands and for all channels) per subject_and_tasks
    """
    
    # Initialize a list to store processed data for each unique subject+segment combination 
    all_bands_vectors = [] 

    # Iterate over all combinations of (subject, subtask) and populate 'all_bands_vectors' with numpy array 'sub_bands_array' containing processed data for each subject_and_tasks
    for pair in subjects_and_tasks:  
        # Construct the path pointing to where processed data for (subject,task) is stored         
        subject, task = pair[0].rstrip(), pair[1] 
        path_to_processed_data = os.path.join(f'{processed_data_dir}', f'sub-{subject}', 'ses-01', 'eeg', 'bandpowers', f'{freq_bands_type}_{task}.csv')
        
        # Create a 2D list to which the read data will be added
        subject_and_task_bands_list = []
        
        # Read csv file and saves each the data to f_bands_list
        with open(path_to_processed_data, 'r') as file:
            reader = csv.reader(file)
            for frequency_band in reader:  
                subject_and_task_bands_list.append([float(f) for f in frequency_band])              
        
        # Convert list to array
        subject_and_task_bands_array = np.array(subject_and_task_bands_list)

        # Normalize each band
        if normalization: 
            ch_tot_powers = np.sum(subject_and_task_bands_array, axis = 0)
            subject_and_task_bands_array = subject_and_task_bands_array / ch_tot_powers[None,:]
        
        subject_and_task_bands_vector = np.concatenate(subject_and_task_bands_array.transpose())
        
#      Validate subject_and_task_bands_vector length:
        if freq_bands_type == 'thin':
            assert len(subject_and_task_bands_vector) == 5696, f"Processed data for subject {subject} does not have the expected length when using thin frequency bands."
        elif freq_bands_type == 'wide':
            assert len(subject_and_task_bands_vector) == (64 * len(wide_bands)), f'Processed data for subject {subject} does not have the expected length when using wide frequency bands.'
            
        # Add vector to matrix
        all_bands_vectors.append(subject_and_task_bands_vector)    

    print(f'INFO: Success! Shape of \'all_bands_vectors\' is {len(all_bands_vectors)} x {len(all_bands_vectors[0])}, as expected.')
    return all_bands_vectors

def create_data_frame(all_bands_vectors, subjects_and_tasks):
    """
    Create a dataframe structure to be used by the model_testing and ROC_AUC.py scripts
    
    
    Input parameters
    ----------------
    - all_bands_vector: list of np arrays
            Each row contains the PSD data (for the chosen frquency bands and for all channels) per subject_and_tasks
    - subjects_and_tasks: list of 2-uples
                Contains the combinations of subjects and segments (e.g., (Subject1, Task1_segment1), (Subject1, Task1_segment2), ...)    
    Output
    ------
    - dataframe: panda dataframe
            Each row contains the subject_and_task label, the group which it belongs to, and the PSD data (for the chosen frquency bands and for all channels) per subject_and_tasks
    """
    
    # Create indices for dataframe
    indices = []
    for i in subjects_and_tasks:
        j = i[0].rstrip()+'_'+i[1]
        indices.append(j)
    
    # Convert list to numpy array to dataframe 
    dataframe = pd.DataFrame(np.array(all_bands_vectors, dtype = object), indices ) 
    
    # Add column 'Group'
    groups = []
    for subject in indices:
        if 'P' in subject[2]:
            groups.append(1)
        elif 'C' in subject[2]:
            groups.append(0)
        else:
            groups.append(2) # In case there is a problem
    dataframe.insert(0, 'Group', groups)
    #TODO: horrible bubble-gum quickfix for CV problem
    #fixed the line above so that it works for all tasks
    subs = np.array([s.split('_' + chosen_tasks[0][0:3])[0] for s in indices]) 
    dataframe.insert(1, 'Subject', subs)
    
    return dataframe

def export_data(dataframe, metadata):
    """
    Creates a pickle object containing the csv and the metadata so that other scripts using the CSV data can have the information on how was the data collected (e.g., input arguments or other variables).
    
    Input parameters
    ----------------
    - dataframe: pandas dataframe
            Each row contains the subject_and_task label, the group which it belongs to, and the PSD data (for the chosen frquency bands and for all channels) per subject_and_tasks
    - metadata: dictonary
                Contains the input arguments parsed when running the script     
    Output
    ------
    - "output.pkl": pickle object
            pickle object which contains the dataframe and the metadata
    """
    with open("output.pickle", "wb") as f:
        pickle.dump((dataframe, metadata), f)
    print('INFO: Success! Processed data has been read in and parsed into dataframe.csv. CSV data and metadata have been bundled into file "output.pickle".')
    
    
if __name__ == '__main__':
    # Save time of beginning of the execution to measure running time
    start_time = time.time()
    
    # Add arguments to be parsed from command line    
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, help="ec, eo, PASAT_1 or PASAT_2", default="PASAT_1")
    parser.add_argument('--freq_bands_type', type=str, help="Define the frequency bands. 'thin' are 1hz bands from 1 to 90hz. 'wide' are conventional delta, theta, etc. Default is 'thin'.", default="thin")
    parser.add_argument('--normalization', type=bool, help='Normalizing of the data from the channels', default=True)
    #parser.add_argument('--threads', type=int, help="Number of threads, using multiprocessing", default=1) #skipped for now
    args = parser.parse_args()
    
    #Create dictonary with metadata information
    metadata_info = {"task": args.task, "freq_bands_type": args.freq_bands_type, "normalization": args.normalization}
    # Print out the chosen configuration
    if args.normalization == True:
        print(f"\nReading in data from task {args.task}, using {args.freq_bands_type} frequency bands. Data will be normalized. \n")
    else:
        print(f"\nReading in data from task {args.task}, using {args.freq_bands_type} frequency bands. Data will NOT be normalized. \n")    
    
    # Execute the submethods:
    # 1 - Define subtasks according to input arguments
    chosen_tasks = define_subtasks(args.task)
    
    # 2 - Read in the list of subjects from file subjects.txt
    subjects = read_subjects()
    
    # 3 - Read in list of subjects from file and create subjects_and_tasks list
    subjects_and_tasks = create_subjects_and_tasks(chosen_tasks, subjects)
    
    # 4 - Read in processed data from file and create list where each row contains all the frquency bands and all channels per subject_and_task
    all_bands_vectors = read_data(subjects_and_tasks, args.freq_bands_type, args.normalization, processed_data_dir)
    
    # 5 - Create dataframe
    dataframe = create_data_frame(all_bands_vectors, subjects_and_tasks)

    # 6 - Outputs the dataframe file with metadata to be used by 02_plot_processed_data.py and 03_fit_classifier_and_plot.py   
    export_data(dataframe = dataframe, metadata = metadata_info)
    
    # Calculate time that the script takes to run
    execution_time = (time.time() - start_time)
    print('\n###################################################\n')
    print(f'Execution time of 01_read_processed_data.py is: {round(execution_time,2)} seconds\n')
    print('###################################################\n')
