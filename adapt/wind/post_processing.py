import os
import pandas as pd
import pickle as pkl
import numpy as np
# get the switch time to next wp in each of each folder
switch_dt  = [root.split("/")[-1] for root,subdir,files in os.walk(os.getcwd(),topdown=True) if not len(subdir)]

dirs    = [root for root,subdir,files in os.walk(os.getcwd(),topdown=True) if not len(subdir)]
ndir = len(dirs)

files  = [files for root,subdir,files in os.walk(os.getcwd(),topdown=True) if not len(subdir)]

col = ["simt", "simtime", "acid",  "actype", "actwp", "actrtawp", "rta",
       "rta - simt", "alt", 'tas', "cas", "gs", "fuel_mass", "mass"]  # logged data

hitting_probability = []

# Run over directories
for i in range(ndir):

    ifiles = files[i]
    idir   = switch_dt[i]

    total           = 0
    reached         = 0
    missed          = 0
    fuel_used       = 0

    for file in ifiles:

        flightid    = file.split("_")[2]
        flight_date = file.split("_")[3]

        raw_data = pd.read_csv(open(os.path.join(dirs[i],file), "rb"),skiprows=8,names=col)
        flight_tstart = raw_data.iloc[0].simtime

        flight_datetime_start = pd.to_datetime(" ".join([flight_date, flight_tstart]))

        # way-points with rta
        waypoints_rta = raw_data.groupby(['actrtawp','rta']).size().reset_index()
        waypoints_rta = waypoints_rta.drop([0],axis=1)
        nwaypoints = waypoints_rta.shape[0]
        total      += nwaypoints

        waypoints_arrival = raw_data.iloc[waypoints_rta.actrtawp][["simt","simtime"]].reset_index()

        waypoints = pd.merge(waypoints_rta,waypoints_arrival,on=waypoints_rta.index)
        waypoints = waypoints.drop(['key_0','index'],axis=1)
        # ADD date to rta time

        waypoints['date'] = pd.DataFrame([flight_date]*nwaypoints,index=waypoints_rta.index)
        waypoints['datetime_rta']       = waypoints[['date','rta']].apply(" ".join,axis=1)
        waypoints['datetime_arrival']   = waypoints[['date','simtime']].apply(" ".join,axis=1)

        waypoints['trta']       = (pd.to_datetime(waypoints['datetime_rta']) - flight_datetime_start)/np.timedelta64(1,'s')
        waypoints['difftime']   = waypoints['simt'] - waypoints['trta']

        waypoints['tw_in+']      = waypoints['difftime'] <= 66
        waypoints['tw_in-']      = waypoints['difftime'] >= -6

        waypoints['tw_in']       = waypoints['tw_in+']  & waypoints['tw_in-']

        results = waypoints['tw_in'].value_counts()

        if results.size == 1 and results.index[0]:
            reached += results[results.index[0]]
        elif results.size == 1 and not results.index[0]:
            missed += results[results.index[0]]
        else:
            reached += results[True]
            missed += results[False]

        fuel_used += raw_data['fuel_mass'].iloc[-1]

    hitting_probability.append([idir,reached,missed,reached+missed, total, round(fuel_used,2)])

print(pd.DataFrame(hitting_probability,columns=["parameters","tw_fullfiled","tw_missed","tw_total","total","fuel_total"]))
