import pandas as pd
import os,datetime,fnmatch
import numpy as np

if __name__ == "__main__":

    tw_type = "symmetric"

    dir_ddr = "ddr_{}".format(tw_type)
    dir_ddr_path = os.path.join(os.getcwd(),"input",dir_ddr)

    wind_path = "input/netcdf"

    # the higher level cruise duration
    trajectory_cruise = []

    for root,dirs,files in os.walk(dir_ddr_path):

        for file in files:
            if file.endswith(".csv"):

                # Load file
                file_ddr_path = os.path.join(dir_ddr_path,file)
                data = pd.read_csv(open(file_ddr_path, 'rb'), parse_dates=True,skip_blank_lines=True)

                # Waypoints in HL cruise
                idx_hl = data["fl"]  == data["fl"].max()
                data = data[idx_hl].reset_index(drop=True)
                data["time_over"] = pd.to_datetime(data['time_over'], dayfirst="True")

                if data.shape[0] <= 1 :
                    pass
                else:
                    print(file)

                    """ Identify trajectories that already have a wind downloaded"""
                    date_departure = data["time_over"].iloc[0].date()
                    delta_time = datetime.timedelta(days=1)
                    # data on which the analysis is made
                    forecast_analysis_date = (date_departure - delta_time).strftime("%Y%m%d")
                    # analysis time
                    t = np.where(data["time_over"].iloc[0].hour >= 12,"12","00")

                    filename  = f"ecmwf_pl_{forecast_analysis_date}_{t}_*.nc"
                    if not os.path.isfile(os.path.join(os.getcwd(),wind_path,filename)):
                        if (data.order.iloc[1:].reset_index(drop=True) - \
                           data.order.iloc[:-1].reset_index(drop=True)).nunique() == 1:
                            cruise_duration = (data.time_over.iloc[-1] - data.time_over.iloc[0]).total_seconds()/60.
                            trajectory_cruise.append([file.split(".")[0],data.time_over[0].date(),cruise_duration])

    trajectory_cruise = pd.DataFrame(trajectory_cruise,columns=["acid","cruise_duration"])
    trajectory_cruise = trajectory_cruise[trajectory_cruise["cruise_duration"] > 20.]
    trajectory_cruise = trajectory_cruise.sort_values("acid").reset_index(drop=True)

    trajectory = pd.read_excel(open(os.path.join(os.getcwd(),"input","trajectoryList-{}.xlsx".format(tw_type)), 'rb'))
    trajectory = trajectory.set_index("acid")

    trajectory = trajectory.loc[trajectory_cruise["acid"].values]

    trajectory = trajectory.loc[np.logical_and(trajectory.opening == 7,trajectory.closing== 8)]

    trajectory["cruise_duration"] = trajectory_cruise.set_index("acid")["cruise_duration"]
    trajectory["date"]            = trajectory_cruise.set_index("acid")["date"]

    trajectory.to_excel(os.path.join(os.getcwd(),"input","trajectoryList-{}-hlcruise.xlsx".format(tw_type)))
