import numpy as np
import os
import pandas as pd
import fnmatch
import pickle
from adapt.scripts import ddrToScn

col = ["simt", "acid", "wfile",  "ens", "wfile1", "actype", "lat", "lon", "alt", 'tas', "cas", "gs", "fuel_mass",
       "mass"]  # logged data

col1 = ["simt", "acid", "wfile",  "ens", "actype", "lat", "lon", "alt", 'tas', "cas", "gs", "fuel_mass",
       "mass"]  # logged data
# adapt .log files storage
simData = os.path.join(os.getcwd(), "adapt/output/WPTLOG")

df_ensemblemean = []

for root, dirs, files in os.walk(simData):

    if len(files) and not dirs:
        # find pickle files in directory
        pkl_files = [os.path.join(root, f) for f in files if fnmatch.fnmatch(f, "*.pkl")]  #

        for file in pkl_files:
            raw_data = pickle.load(open(file,"rb"))

        # add header to dataframe of ensembles.
        if raw_data.columns.__len__() == 13:
            raw_data.columns = col1
            raw_data = raw_data.drop(columns=['wfile', 'acid', 'actype'])
            afms_dt = "time"
            npw = "over"

        else:
            raw_data.columns = col
            raw_data = raw_data.drop(columns=['wfile', 'wfile1', 'acid', 'actype'])

            afms_dt = root.split("/")[-1][6:9]
            npw = file.split("/")[-1].split("_")[3][-1]

        # Create new DataFrame that contains only the mean values at each way-point
        raw_data        = raw_data.reset_index()
        ensembleMean    = raw_data.groupby('index').mean()

        ensembleMean_param = ensembleMean[["simt", "fuel_mass"]]

        col_new = ["simt_{}_{}".format(afms_dt,npw),"fuel_{}_{}".format(afms_dt,npw)]
        ensembleMean_param.columns = col_new

        df_ensemblemean.append(ensembleMean_param)

df_ensemble = pd.concat(df_ensemblemean,axis=1)

# Load the data from the DDR such that we get the time over the way-point from the planned trajectory
ddr_file = "data/ddr/ADH931.csv"
scenario = ddrToScn.parseDDR(ddr_file, cruise=True)

epoch       = scenario.data.time_over.iloc[0]
time_over_s = (scenario.data.time_over - epoch) / np.timedelta64(1, 's')
df_ensemble["time_over"] = time_over_s

# # Add the [time_over - tw/2 ; time_over + tw/2]
# df_ensemble["time_over_+"] = df_ensemble["time_over"] + 30
# df_ensemble["time_over_-"] = df_ensemble["time_over"] - 30
#
# # Add the time_over from the simulation using the average speed
# df_ensemble["simt_time_over+"] = df_ensemble["simt_time_over"] + 1500
# df_ensemble["simt_time_over-"] = df_ensemble["simt_time_over"] - 30

# difference between simt-tie-over and time_over
# df_ensemble["d(time_over - simt_time_over"] = df_ensemble["time_over"] -  df_ensemble["simt_time_over"]

# different AFMS update rates: 1,2,3 minutes for five waypoints
df_analyis_list = []

simt_1 = []
for col in df_ensemble.columns:
    if fnmatch.fnmatch(col,"fuel*"):
        simt_1.append(col)

df_ensemble_a1 = df_ensemble[simt_1]

df_ensemble_a1.to_excel("wpt_adh931_tw1_fuel.xlsx", sheet_name='Sheet1',
                   na_rep='', float_format=None, columns=None,
                   header=True, index=True, index_label=None,
                   startrow=0, startcol=0, engine=None, merge_cells=True,
                   encoding=None, inf_rep='inf', verbose=True, freeze_panes=None)




