import os,logging,datetime
import bluesky.traffic.performance.bada.coeff_bada as coefficient
from   bluesky.tools import aero, geo
import pandas as pd
from scripts.download_forecast import DownloadWind
import numpy as np

def _import_data(fpath, cruise):
    """

    :param  fpath: Complete path of file which contains trajectory data in ddr_original format.
            cruise: Select only high level cruise.
    :return:  Pandas data frame of trajectory way-points

    """
    data = pd.read_csv(fpath, delimiter=',', skipinitialspace=True)  # Import DDR2 data into a panda dataframe
    # Convert the time over waypoint from string to a panda Timestamp object
    data.time_over = pd.to_datetime(data['time_over'], dayfirst="True")

    # Set as dataframe index the waypoint order
    data = data.set_index('order')

    # Delete columns that are empty and do not provide any value
    data = data.drop(["trajectory_id","distance","visible","id","rel_dist","coords"], axis=1)

    # Change name of Dataframe columns
    data.rename(columns={data.columns[5]: "x_coord",
                         data.columns[6]: "y_coord"},
        inplace=True)

    # Only get cruise waypoints
    # BADA cruise refernce mach used after FL140 => FL140 change cruise way-point threshold
    if cruise:
        data = data.loc[data.fl == data.fl.max()]
        data = data.reset_index(drop=True)

    return data

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    generate_files = True

    bluesky_scn_path = "/Users/Claudia/Documents/5-MSc-2/bluesky/scenario"
    data_set_path = os.path.join(os.getcwd(),"input", "ddr")
    sim_scn_path  = os.path.join(bluesky_scn_path,"asymmetric",
                                 datetime.datetime.now().strftime("%Y%m%d"),"individual")

    if not os.path.isdir(sim_scn_path):
        print()
        print('Directory not found.')
        os.makedirs(sim_scn_path)
        print('A default version will be generated')
        print()

    constrain = []
    trajectory_list = pd.read_excel(os.path.join(os.getcwd(),"input", "xlsx","final.xlsx"))
    trajectory_list = trajectory_list.set_index("acid")

    trajectory_list["waypoints"]            = 0.
    trajectory_list["CAS_cr"]               = 0.
    trajectory_list["M_cr"]                 = 0.
    trajectory_list["CAS_initial"]          = 0.
    trajectory_list["CAS_max"]              = 0.
    trajectory_list["M_max"]                = 0.
    trajectory_list["alt_transition"]       = 0.
    trajectory_list["FL"]                   = 0.

    coefficient.init(os.path.join("/Users/Claudia/Documents/5-MSc-2/bluesky",
                                  "data/performance/BADA"))
    day_before_departure = 1

    """ Loop through the DDR trajectories to create scn files"""

    tw_duration      = ["01","60","deterministic","probabilistic"]
    departure_delay  = [0,5,10,15,20]

    """ Configure the paths for the wind data"""

    netcdf_path = os.path.join(os.getcwd(), 'input','netcdf')
    grib_path   = os.path.join(os.getcwd(), "input","grib")

    """ """
    waypoints = pd.DataFrame(columns=trajectory_list.index,index=np.arange(0,19,1))
    for file in os.listdir(data_set_path):

        file_path = os.path.join(data_set_path,file)
        print("trajectory >>>", os.path.splitext(file)[0])

        data             = _import_data(file_path,cruise=True)
        acid             = os.path.splitext(file)[0]  # get the acid from file title
        date_start       = data.iloc[0].time_over  # start datetime
        date_end         = data.iloc[-1].time_over # end datetime
        ac_type          = trajectory_list.loc[acid]["ac_type"]
        tws              = trajectory_list.loc[acid][tw_duration]
        rta_wpts         = None

        h_trans = aero.crossoveralt(coefficient.getCoefficients(ac_type)[1].CAScl2[1] * aero.kts,
                                    coefficient.getCoefficients(ac_type)[1].Mcl[1])
        h       = data.fl[0] * 100 * aero.ft

        Mcr = coefficient.getCoefficients(ac_type)[1].Mcr[1]

        if h > h_trans:
            cascr  = aero.mach2cas(Mcr,h) / aero.kts
        else:
            cascr = coefficient.getCoefficients(ac_type)[1].CAScr2[1]

        date_departure  = date_start.date()
        delta_time      = datetime.timedelta(days=day_before_departure)
        # Data on which the analysis is made
        forecast_analysis_date   = date_departure - delta_time

        if date_start.hour >= 12:
            forecast_analysis_time = "12"
        else:
            forecast_analysis_time = "00"

        # Step in the future from which to begin forecast retrieval
        forecast_step_start = datetime.timedelta(days=day_before_departure).total_seconds()/3600
        # ECMWF steps in an ensemble forecast analysis
        interval = 6  # ECMWF interval of forecast analysis

        if (date_start.hour < 12 <= date_end.hour) or \
           (date_start.hour < 24 <= date_end.hour):
            forecast_steps =  np.arange(start=forecast_step_start,
                                           stop=forecast_step_start + interval*4,
                                           step=interval)
            time_forecast_step = "18"
        else:
            forecast_steps =  np.arange(start=forecast_step_start,
                                           stop=forecast_step_start + interval*3,
                                           step=interval)
            time_forecast_step = "12"

        # Download the wind data for this trajectory
        DownloadWind(date_departure,
                     forecast_analysis_date,
                     forecast_analysis_time,
                     forecast_steps,
                     grib_path,netcdf_path)

        # Heading from the start waypoint to the next waypoint
        hdg, _ = geo.qdrdist(data.iloc[0]['x_coord'],
                             data.iloc[0]['y_coord'],
                             data.iloc[1]['x_coord'],
                             data.iloc[1]['y_coord'])

        wp_freq = 300
        rta_waypoints = []  # list of way-points that have an RTA constraint

        current_wp   = data.index[-1]                   # start from first way-point
        rta_waypoints.append(current_wp)
        current_time = date_end

        # as long as there are way-points
        while current_wp >  data.index[0]:

            # calculate the number of seconds from current way-point to all the other way-points left in
            # the trajectory
            wp_timedelta = (current_time - data['time_over'][:current_wp]).dt.total_seconds()
            wp_timedelta = wp_timedelta[wp_timedelta > int(wp_freq)]

            if not wp_timedelta.size:
                current_wp = 0
            else:
                current_wp   = wp_timedelta.index[-1]
                current_time = data['time_over'][current_wp]
                rta_waypoints.append(current_wp)

        rta_waypoints = sorted(rta_waypoints)

        if 0 in rta_waypoints:
            rta_waypoints.remove(0)

        trajectory_list["waypoints"][acid]       = data.shape[0] - 1
        trajectory_list["CAS_cr"][acid]          = coefficient.getCoefficients(ac_type)[1].CAScr2[1]
        trajectory_list["M_cr"][acid]            = aero.mach2cas(Mcr,h) / aero.kts
        trajectory_list["CAS_initial"][acid]     = cascr
        trajectory_list["CAS_max"][acid]         = coefficient.getCoefficients(ac_type)[1].VMO
        trajectory_list["M_max"][acid]           = aero.mach2cas(coefficient.getCoefficients(ac_type)[1].MMO,h) / aero.kts
        trajectory_list["alt_transition"][acid]  = float(h_trans / aero.ft / 100.)
        trajectory_list["FL"][acid]              = float(h / aero.ft / 100.)

        if generate_files:
            for delay in departure_delay:

                departure_time = date_start + datetime.timedelta(minutes=delay)

                for tw in tws.index:

                    scn_file_name = ".".join(["_".join([tw,
                                                        acid,
                                                        date_start.strftime("%Y%m%d"),
                                                        str(delay),
                                                        forecast_analysis_time,
                                                        time_forecast_step]),'scn'])

                    scn_file_path = os.path.join(sim_scn_path,scn_file_name)
                    with open(scn_file_path,"w") as scnfile:

                        # Initialise simulation
                        scnfile.write("00:00:00.00>HOLD \n" + \
                                      "00:00:00.00>DATE {}\n".format(departure_time.strftime("%d %m %Y %H:%M:%S.00")) + \
                                      '00:00:00.00>CRE ' + ", ".join([acid, ac_type,
                                                                      str(data.iloc[0].x_coord),
                                                                      str(data.iloc[0].y_coord),
                                                                      str(hdg),
                                                                      str(data.iloc[0].fl) + "00",
                                                                      str(cascr) + "\n"]))

                        # Define waypoints

                        x_coord = data[1:].x_coord.apply( lambda x: str(x))
                        y_coord = data[1:].y_coord.apply( lambda x: str(x))
                        wp_name = ['wpt_{}'.format(idx) for idx in x_coord.index.values]

                        define_wpts = '0:00:00.00>DEFWPT ' + pd.Series(wp_name,index=x_coord.index.values) + \
                                      " " + x_coord + " " + y_coord + "\n"

                        for row in define_wpts:
                            scnfile.write(row)

                        fl = data[1:].fl.apply( lambda x: "FL"+str(x))
                        add_wpts = '0:00:00.00>ADDWPT ' + acid + " " + pd.Series(wp_name,index=x_coord.index.values) + \
                                   " " + fl + " \n"

                        for row in add_wpts:
                            scnfile.write(row)

                        rta_times           = data['time_over'].iloc[rta_waypoints]
                        wp_after_departure  = (rta_times - departure_time).dt.total_seconds() > 0
                        rta_waypoints       = list(rta_times[wp_after_departure].index)

                        time = data.loc[rta_waypoints].time_over.apply( lambda x: x.strftime("%d %m %Y %H:%M:%S.00"))
                        rta_wpt_name = ['wpt_{}'.format(idx) for idx in rta_waypoints]

                        rta_cmd = "0:00:00.00>RTA {} ".format(acid) + pd.Series(rta_wpt_name,index=rta_waypoints)  \
                                + " " + time + " \n"

                        for row in rta_cmd:
                            scnfile.write(row)

                        scnfile.write("0:00:00.00>TW {} ".format(acid) + str(tws[tw]*60) + "\n")
                        scnfile.write("0:00:00.00>AFMS {} ".format(acid) + " ON\n")
                        scnfile.write("0:00:00.00>CRELOG WINDLOG 1.0\n")
                        scnfile.write("0:00:00.00>WINDLOG ADD id,lat,lon,alt,gs,tas,traf.pilot.tas,"
                                      "cas,trk,hdg,bank,traf.ax,traf.swhdgsel,traf.wind.current_ensemble\n")
                        scnfile.write("0:00:00.00>WINDLOG ON\n")
                        scnfile.write("0:00:00.00>WPTLOG ON\n")
                        scnfile.write("0:00:00.00>lnav {} ON \n" \
                                       "0:00:00.00>vnav {} ON \n" \
                                       "0:00:00.00>op \n" \
                                       "0:00:01.00>ff\n".format(acid,acid))

                wp = ""
                for rta in rta_waypoints:
                    wp = wp + str(rta) + "_"
                constrain.append([acid, delay, wp])
        waypoints[acid] = data.time_over

    data_1 = pd.DataFrame(constrain,columns=["acid","delay","tw"])
    data_1 = data_1.set_index(["acid"])
    data_1 = data_1.pivot(columns="delay")

    waypoints = waypoints.transpose()

    waypoints.to_excel(os.path.join(os.getcwd(), "output", "wp_20191119.xlsx"))
    data_1.to_excel(os.path.join(os.getcwd(), "output", "WPTW.xlsx"))
    trajectory_list.to_excel(os.path.join(os.getcwd(), "input", "final.xlsx"))
