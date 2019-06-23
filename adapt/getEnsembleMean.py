import numpy as np
import os, datetime
import pandas as pd


dirOutput = "output/wind_sensitivity_analysis/rta/wpt_4"

col = ["simt", "acid", "wfile",  "ens", "actype", "lat", "lon", "alt", 'tas', "cas", "gs", "fuel_mass",
       "mass"]  # logged data

for dirpath, dirnames, files in os.walk(dirOutput):
    if len(files) is not 0:

        ensembleMembers = pd.DataFrame(columns=col)
        print(f'Found directory: {dirpath}')
        # Load all of the files run with the same ensemble into one dataframe
        for file_name in files:

            data = pd.read_csv(os.path.join(dirpath,file_name), sep=",", header=None,names=col,skiprows=8)
            ensembleMembers = pd.concat([ensembleMembers, data])

        acid = ensembleMembers.acid.iloc[0]
        ensembleMembers = ensembleMembers.drop(columns=['wfile','acid','actype'])

        # Create new DataFrame that contains only the mean values at each way-point
        ensembleMembers = ensembleMembers.reset_index()
        ensembleMean    = ensembleMembers.groupby('index').mean()

        ensembleMean.to_csv("ADH931_{}.csv".format(dirpath.split("/")[-1].split("_")[-1]),
                                columns=np.array(ensembleMean.columns),index=True)


