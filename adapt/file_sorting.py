"""
BlueSky output file system storage
=========================================================================
    * move_output()

    Moves the files obtained as output from the perturbed
    forecast simulations form the BlueSky default folder and stores them in a
    corresponding directory to be used for analysis later on. The structure of
    the directory tree is shown below.

    output
     |
     +-- logger type
         |
         +-- acid
            |
            +-- creation date

    * pkl_arc()

    This module completes 2 tasks
        1) archives all the data files in the lowest subdirectories of the
        above directory tree into one .zip per time window type.
        2) pickles a DataFrame that contains data from all the files of the
        same time window type.

"""
import shutil
import os
import pandas as pd
import pickle
import logging
import fnmatch
import zipfile

def move_log_files():

    # Define the BlueSky output folder from which to move simulation results.
    root = "/Users/Claudia/Documents/5-MSc-2/bluesky"
    bs_output = os.path.join(root,"output")

    # List the files in the BlueSKy output folder
    sim_files = [file for file in os.listdir(bs_output) if file.endswith(".log")]

    # Create a new folder to store data in based on the directory tree from above
    log_type = [file.split("_")[0] for file in sim_files] # Log type upper dir
    acid = ["_".join(file.split("_")[2:5]) for file in sim_files] # id of aircraft that has been analysed.
    creation_date = [file.split("_")[-2] for file in sim_files]  #

    # make the target directory
    for l in set(log_type):
        for id in set(acid):
            for date in set(creation_date):
                dir_name = os.path.join(root,"adapt","output",l,id,date)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)

    # get src file path
    src_path = [os.path.join(bs_output,file) for file in sim_files]

    # new path for each file
    dst_path = [os.path.join(root,"adapt","output",log_type[idx],acid[idx],creation_date[idx])
                for idx,file in enumerate(sim_files)]

    # move the files
    for idx,file_path in enumerate(src_path):
        if os.path.isfile(file_path):
            shutil.move(file_path,dst_path[idx])


def windlog_to_pkl():

    # adapt .log files storage
    root = os.getcwd()
    simData = os.path.join(root,"output")
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    # TODO update
    twTypes = ['None','rta']

    for root,dirs,files in os.walk(simData):

        if files and not dirs:
            logging.info('%s directory with %s subdirectory and %s files', root, len(dirs), len(files))

            for tw_type in twTypes:
                logging.info('%s time window type data', tw_type)

                # rename all the files in the directory that are .log
                sim_path_files = [f for f in glob.glob(os.path.join(root, '*{}*.log'.format(twTypes)))]

                if sim_path_files:

                    # List containing all the df of the log files
                    df_list = []

                    # pickle filename
                    filename = "_".join(sim_path_files[0].split("_")[:-1])

                    pkl_path  = filename + '.pkl'

                    # check if it already exists
                    if not os.path.isfile(pkl_path ):
                        logging.info('pickling data in %s', filename)

                    # load all the corresponding files
                        for file in sim_path_files:
                            read_file = pd.read_csv(os.path.join(simData, file), header=1)
                            df_list.append(read_file)

                        frame = pd.concat(df_list,axis=0)
                        pickle.dump(frame,open(pkl_path ,'wb'))

                    # create zip path
                    zip_path = os.path.join(root, filename + '.zip')

                    if not os.path.isfile(zip_path):
                        # zip log files
                        logging.info('zipping data in %s', filename + '.zip')

                        with zipfile.ZipFile(zip_path, 'w') as new_zip:
                            for file in sim_path_files:
                                new_zip.write(file,os.path.basename(file))

                    if os.path.isfile(zip_path) and  os.path.isfile(pkl_path):
                        for file in sim_path_files:
                            os.remove(file)

def log_to_pkl():

    # adapt .log files storage
    root = os.getcwd()
    simData = os.path.join(root,"output")
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    for root,dirs,files in os.walk(simData):

        if len(files) and not dirs:

            logging.info('%s directory with %s subdirectory and %s files', root, len(dirs), len(files))

            # # rename all the files in the directory that are .log
            # rename all the files in the directory that are .log
            sim_path_files = [os.path.join(root,f) for f in files if fnmatch.fnmatch(f,"*.log")]            #


            if sim_path_files:

                # List containing all the df of the log files
                df_list = []

                # pickle filename
                filename = "_".join(sim_path_files[0].split("_")[:-1])

                pkl_path  = filename + '.pkl'

                # check if it already exists
                logging.info('pickling data in %s', filename)

                # load all the corresponding files
                for file in sim_path_files:
                    read_file = pd.read_csv(os.path.join(simData, file), header = None, skiprows=8)
                    df_list.append(read_file)

                frame = pd.concat(df_list,axis=0)
                pickle.dump(frame,open(pkl_path ,'wb'))


if __name__ == "__main__":
    move_log_files()
    log_to_pkl()
