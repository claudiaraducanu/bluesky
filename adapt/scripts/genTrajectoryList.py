import  bluesky.traffic.performance.bada.coeff_bada as coefficient
import pandas as pd
import os

def getTrajectoryList(filename,paths):

    """ Get network schedule results to get aircraft type and time window"""
    trajectory_list = pd.read_csv(os.path.join(paths["input_path"],"dataResultsRemon.csv"), header=[0,1], skiprows=-1)

    # select only desired columns
    trajectory_list = trajectory_list[trajectory_list.columns[[0,1,2,3,11,16]]]
    trajectory_list.columns = ["acid", "orig", "dist","ac_type","deterministic", "probabilistic"]
    trajectory_list = trajectory_list.iloc[:-1]

    # make the acid name consists of only letters and set index
    trajectory_list["acid"] = trajectory_list["acid"].str.split(" ", n=1, expand=True)[0]
    trajectory_list["ac_type"] = trajectory_list["ac_type"].str.split(" ", n=1, expand=True)[0]

    # convert the time window to dtype numeric
    trajectory_list["deterministic"] = pd.to_numeric(trajectory_list["deterministic"])
    trajectory_list["probabilistic"] = pd.to_numeric(trajectory_list["probabilistic"])

    # add the cas airspeed for each aircraft trajectory
    trajectory_list["casCr"] = 0
    drop_trajectories        = [] # trajectories to drop because BADA does not have a flight for them
    coefficient.init(bada_path=paths["bada_path"])

    for index, row in trajectory_list.iterrows():
        syn, coeff = coefficient.getCoefficients(row["ac_type"])
        if syn:
            trajectory_list["casCr"][index] =  coeff.CAScr2[0]
        else:
            drop_trajectories.append(index)

    trajectory_list = trajectory_list.drop(trajectory_list.index[drop_trajectories])
    trajectory_list = trajectory_list.set_index("acid")

    # save to excel
    with pd.ExcelWriter(filename) as writer:
        for n, df in enumerate([trajectory_list]):
            df.to_excel(writer)
        writer.save()