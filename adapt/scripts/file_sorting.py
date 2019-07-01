"""
BlueSky output file system storage
=========================================================================

    output
     |
     +-- simulation date
         |
         +-- logger type
            |
            +-- time window type

"""
import shutil
import os
import pandas as pd
import pickle as pkl
import fnmatch

def fdata(filename):

    file = os.path.splitext(filename)[0].split("_")

    filedata = {'log'           : file[0],
                'tw'            : file[1],
                'acid'          : file[2],
                'flight_date'   : file[3],
                'sim_date'      : file[6]}

    return filedata

def sortandpickle(sim_files,paths):

    # Create a new folder to store data in based on the directory tree from above
    log_type = [fdata(file)['log'] for file in sim_files]  # log type upper dir
    sim_date = [fdata(file)['sim_date'] for file in sim_files]  # type of simulation
    acid = [fdata(file)['acid'] for file in sim_files]  # id of aircraft that has been analysed.
    tw = [fdata(file)['tw'] for file in sim_files]  # id of aircraft that has been analysed.

    # Move data after processing the target directory
    for log in set(log_type):

        for date in set(sim_date):

            for tw in set(tw):

                dir_name = os.path.join(paths["output_path"], log, date, tw)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)

                for ac in set(acid):

                    print("simulation type >>>", log, tw, date, ac)

                    sim_path_files = [os.path.join(paths["output_path"], file) for file in sim_files
                                      if fnmatch.fnmatch(file, '{}_{}_{}*{}*'.format(log, tw, ac, date))]

                    if len(sim_path_files):
                        # List containing all the df of the log files
                        df_list = []

                        # # pickle filename
                        fileName = "_".join([log, date, tw, ac])
                        pkl_path = os.path.join(paths["output_path"], fileName + '.pkl')

                        # check if it already exists
                        if not os.path.isfile(pkl_path):

                            # load all the corresponding files
                            for file in sim_path_files:
                                read_file = pd.read_csv(file, header=None, skiprows=8)
                                df_list.append(read_file)
                                shutil.move(file, dir_name)

                            frame = pd.concat(df_list, axis=0)
                            pkl.dump(frame, open(pkl_path, 'wb'))

