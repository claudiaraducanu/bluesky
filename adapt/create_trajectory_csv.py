import pandas as pd
import os

if __name__ == "__main__":

    tw_type = "symmetric"
    # Trajectories file path
    filename_trajectories = os.path.join(os.getcwd(),"input","Data2017AllTrajectories_EDDM -{}.csv".format(tw_type))

    data = pd.read_csv(open(filename_trajectories,'rb'),parse_dates=True,
                                skip_blank_lines = True)
    data = data.drop(['Unnamed: 18', 'Unnamed: 19', 'Unnamed: 20','Unnamed: 21',
                      'Unnamed: 22', 'Unnamed: 23', 'Unnamed: 24','Unnamed: 25'],axis=1)

    columns = ["trajectory_id",
              "geopoint_id" ,
              "distance" ,
              "fl" ,
              "time_over" ,
              "type" ,
              "rel_dist" ,
              "visible" ,
              "order" ,
              "id",
              "coords",
              "type" ,
              "st_x(gpt.coords)",
              "st_y(gpt.coords)"]

    # set index as the trajectory uuid
    data = data.set_index("uuid_of_flight")

    # get the unique trajectories and their number
    trajectories = pd.unique(data.index)
    pd.unique(data.callsign)
    no_trajectories = trajectories.shape[0]

    trajectory_list = []

    for t in trajectories:
        trajectory_list.append([data.loc[t]["callsign"].iloc[0],
                                           data.loc[t]["origin"].iloc[0],
                                           data.loc[t]["destination"].iloc[0],
                                           data.loc[t]["ac_type"].iloc[0],
                                           data.loc[t]["maximum_negative_shift"].iloc[0],
                                           data.loc[t]["maximum_positive_shift"].iloc[0]])

        tdata = pd.DataFrame([],columns=columns)

        tdata["trajectory_id"] = data.loc[t]["callsign"].reset_index(drop=True)
        tdata["geopoint_id"]   = data.loc[t]["waypoint"].reset_index(drop=True)
        tdata["id"]            = data.loc[t]["waypoint"].reset_index(drop=True)
        tdata["time_over"]     = data.loc[t]["time_over"].reset_index(drop=True)
        tdata["fl"]            = data.loc[t]["flight_level"].reset_index(drop=True)
        tdata["order"]              = data.loc[t]['order_sequence'].reset_index(drop=True)
        tdata["st_x(gpt.coords)"]   = data.loc[t]["lat"].reset_index(drop=True)
        tdata["st_y(gpt.coords)"]   = data.loc[t]["lon"].reset_index(drop=True)

        tdata = tdata.sort_values(by=['order']).reset_index(drop=True)

        filename_trajectory = os.path.join(os.getcwd(),"input","ddr_{}".format(tw_type),
                                           tdata["trajectory_id"][0] + ".csv")
        tdata.to_csv(path_or_buf=filename_trajectory, sep=',',index=False)

    filename_trajectories = os.path.join(os.getcwd(), "input","trajectoryList-{}.xlsx".format(tw_type))
    trajectory_list = pd.DataFrame(trajectory_list,columns=["acid",
                                                     "orig",
                                                     "dist",
                                                     "ac_type",
                                                     "opening","closing"]).sort_values("acid").reset_index(drop=True)

    trajectory_list.to_excel(filename_trajectories,index=False)


