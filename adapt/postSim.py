import os
import pandas as pd
import pickle as pkl
from netCDF4 import num2date
import fnmatch
import numpy as np
import datetime
from scripts import ddr2scn
from scripts import adaptsettings,file_sorting


def pklfdata(filename):

    file = os.path.splitext(filename)[0].split("_")

    filedata = {'log'           : file[0],
                'tw'            : file[2],
                'acid'          : file[3],
                'sim_date'      : file[1]}

    return filedata


if __name__ == "__main__":

    print()
    print("Processing the simulation data  ")

    """ load the default settings for the postSimulation BlueSky ( paths where data is stored and where to
    store it after the simulation is run"""
    config = adaptsettings.init()

    paths           = config[config.sections()[0]]

    # List the files in the adapt output folder
    files = [file for file in os.listdir(paths["output_path"])
                 if os.path.isfile(os.path.join(paths["output_path"], file))]

    """ Sort and pickle the logged BlueSky data based on (logger,simulation date,time window type,acid)"""
    sim_files = [file for file in files if file.endswith(".log")]

    if len(sim_files):
        # Sort and pickle the ".log"
        file_sorting.sortandpickle(sim_files,paths)

    pklfile =  [file for file in files if file.endswith(".pkl")]

    col = ["simt", "acid", "wfile", "ens", "wfile1", "actype", "lat", "lon", "alt", 'tas', "cas", "gs", "fuel_mass",
           "mass"]  # logged data

    acid    = set([pklfdata(file)['acid'] for file in pklfile])  # id of aircraft that has been analysed.
    dates   = set([pklfdata(file)['sim_date'] for file in pklfile])  # id of aircraft that has been analysed.
    logs     = set([pklfdata(file)['log'] for file in pklfile])  # id of aircraft that has been analysed.

    """ remon results to get aircraft type and time window"""
    trajectory_list = pd.read_csv(os.path.join(paths["input_path"],"dataResultsRemon.csv"), header=None,skiprows=-1)
    trajectory_list = trajectory_list[trajectory_list.columns[:-11]]
    trajectory_list = trajectory_list.iloc[:-1]

    # set dataframe columns
    col_level1 = pd.Series(trajectory_list.iloc[0]).fillna(method='ffill')
    col_level1[col_level1.isna()] = "NAN"
    col_level2  = pd.Series(trajectory_list.iloc[1]).fillna(method='ffill')

    col_mod = list(zip(col_level1,col_level2))

    # dataframe index is ACID
    trajectory_list         = trajectory_list[2:]
    trajectory_list.columns = pd.MultiIndex.from_tuples(col_mod)
    trajectory_list = trajectory_list.set_index([("NAN","Acid")])
    trajectory_list.set_index(pd.Series([index.split()[0] for index in trajectory_list.index]),inplace=True)

    analysed_trajectory_list = trajectory_list.loc[acid]

    analysed_trajectory_list[("01","fuel used")] = None
    analysed_trajectory_list[("01","flight time")] = None
    analysed_trajectory_list[("01","arrival time")] = None
    analysed_trajectory_list[("60","fuel used")] = None
    analysed_trajectory_list[("60","flight time")] = None
    analysed_trajectory_list[("60","arrival time")] = None

    analysed_trajectory_list = analysed_trajectory_list.drop("final mass", axis=1, level=1)
    # analysed_trajectory_list = analysed_trajectory_list.drop("arrival time", axis=1, level=1)

    for log in logs:
        for date in dates:
            for ac in acid:

                analysed_trajectory = trajectory_list.loc[ac]

                ddr_file = os.path.join(paths["ddr_path"],ac) + ".csv"
                scenario = ddr2scn.parseDDR(ddr_file, cruise=True)

                epoch       = scenario.data.time_over.iloc[0]

                analysed_trajectory_list.loc[ac][("NAN","start_time")] = epoch
                analysed_trajectory_list.loc[ac][("NAN","RTA")] = scenario.data.time_over.iloc[-1]

                time_over_s = (scenario.data.time_over - epoch) / np.timedelta64(1, 's')

                pklfile_ac = [file for file in pklfile if fnmatch.fnmatch(file,"{}*{}*{}*".format(log,date,ac))]

                # Create a Pandas Excel writer using XlsxWriter as the engine.
                writer = pd.ExcelWriter(os.path.join(paths["xlsx_path"],
                                                     "{}_{}_{}.xlsx".format(log,date,ac)))

                for ipklfile_ac in pklfile_ac:

                    raw_data = pkl.load(open(os.path.join(paths["output_path"],ipklfile_ac), "rb"))
                    raw_data.columns = col
                    raw_data = raw_data.drop(columns=['wfile','wfile1',"ens",'acid',"lat",
                                                      "lon","alt", 'tas', "cas", "gs","mass"])

                    # Create new DataFrame that contains only the mean values at each way-point
                    raw_data        = raw_data.reset_index()
                    ensembleMean    = raw_data.groupby('index').mean()
                    ensembleMean["time_over"] = time_over_s

                    if pklfdata(ipklfile_ac)['tw'] == "deterministic".upper():
                        tw = int(trajectory_list.loc[scenario.acid]["deterministic"]['TW'])
                    elif pklfdata(ipklfile_ac)['tw'] == "probabilistic".upper():
                        tw = int(trajectory_list.loc[scenario.acid]["probabilistic"]['TW'])
                    else:
                        tw = int(pklfdata(ipklfile_ac)['tw'])

                    analysed_trajectory_list.loc[ac][pklfdata(ipklfile_ac)['tw'].lower()]["TW"] = tw
                    analysed_trajectory_list.loc[ac][pklfdata(ipklfile_ac)['tw'].lower()]["flight time"] = \
                        ensembleMean.simt.iloc[-1]

                    analysed_trajectory_list.loc[ac][pklfdata(ipklfile_ac)['tw'].lower()]["fuel used"] = \
                        ensembleMean.fuel_mass.iloc[-1]

                    analysed_trajectory_list.loc[ac][pklfdata(ipklfile_ac)['tw'].lower()]["arrival time"] = \
                        num2date(ensembleMean.simt.iloc[-1],units='seconds since {}'.
                                 format(epoch.strftime("%Y-%m-%d %H:%M:%S")),
                                 calendar='gregorian')

                    ensembleMean["time_over + tw/2"] = time_over_s + tw/2*60
                    ensembleMean["time_over - tw/2"] = time_over_s - tw/2*60

                    ensembleMean["diff(time_over + tw/2,simt)"] = ensembleMean["time_over + tw/2"]  - \
                                                                  ensembleMean["simt"]
                    ensembleMean["diff(time_over - tw/2,simt)"] = ensembleMean["simt"] - \
                                                                  ensembleMean["time_over - tw/2"]

                    ensembleMean["in-upper"]         = ensembleMean["time_over + tw/2"] > ensembleMean["simt"]
                    ensembleMean["in-lower"]         = ensembleMean["time_over - tw/2"] < ensembleMean["simt"]
                    ensembleMean["in"]               = ensembleMean["in-upper"] & ensembleMean["in-lower"]

                    # Write each dataframe to a different worksheet.
                    ensembleMean.to_excel(writer, sheet_name= pklfdata(ipklfile_ac)['tw'])

                # Close the Pandas Excel writer and output the Excel file.
                writer.save()

    analysed_trajectory_list.set_index("NAN")
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(os.path.join(
        paths["xlsx_path"],"WPTLOG_analysis_{}.xlsx".format(datetime.datetime.now().strftime("%Y%m%d"))))
    analysed_trajectory_list.to_excel(writer)
    writer.save()


