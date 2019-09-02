import os,logging,datetime
import numpy  as np
import pandas as pd
from scripts import adaptsettings,ddr2scn,grib2wind,genTrajectoryList

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    print()
    print("Initialising BlueSky scenario fil1es and retrieving wind data for the trajectories ... ")

    """ load the default settings for the preSimulation BlueSky ( paths where data is stored and where to
    store it after the simulation is run"""
    config = adaptsettings.init()

    paths           = config[config.sections()[0]]
    afms_mode       = config[config.sections()[1]]

    """ select the number of days before departure to retrieve wind from """
    # the default number of days before departure is none

    daysBeforeDeparture = []
    inputDays = input("Enter a list of days before departure separated by a space (e.g 0 1 4 6 ): ")
    print()

    # convert the input from str to int
    if len(inputDays):
        inputDays = inputDays.split()
        daysBeforeDeparture = np.array([int(day) for idx, day in enumerate(inputDays)]    )

    hoursBeforeDeparture = daysBeforeDeparture * 24

    "Logtype"
    logType = 'wptlog'

    currentScndir = os.path.join(paths["scn_path"],logType.upper(),datetime.datetime.now().strftime("%Y%m%d"))

    if not os.path.isdir(currentScndir):
        print()
        print('No {} directory in {} found'.format(logType.upper() + "/" +
                                                   datetime.datetime.now().strftime("Y%m%d"),
                                                   paths["scn_path"]))
        os.makedirs(os.path.join(paths["scn_path"],logType.upper(),datetime.datetime.now().strftime("%Y%m%d")))
        print('A default version will be generated,please do not change')
        print()

    if not os.path.isfile(os.path.join(paths["input_path"], "trajectoryList.xlsx")):
        genTrajectoryList(os.path.join(paths["input_path"], "trajectoryList.xlsx"),paths)

    trajectory_list = pd.read_excel(os.path.join(paths["input_path"], "trajectoryList.xlsx"))
    trajectory_list = trajectory_list.set_index("acid")


    """ Loop through the DDR trajectories to create scn files"""

    for root,dirs,files in os.walk(paths["ddr_path"]):

        for file in files:
            if file.endswith(".csv") and  os.path.splitext(file)[0] in trajectory_list.index:

                print("trajectory >>>", os.path.splitext(file)[0])
                scenario = ddr2scn.parseDDR(os.path.join(root,file))

                scenario.ac_type            = trajectory_list.loc[scenario.acid]["ac_type"]
                scenario.tw_deterministic = trajectory_list.loc[scenario.acid]["deterministic"]
                scenario.tw_probabilistic = trajectory_list.loc[scenario.acid]["probabilistic"]
                cascr = trajectory_list.loc[scenario.acid]["casCr"]

                """Retrieve wind"""
                timeAnalysis,stepEnd = grib2wind.downloadWind(scenario,daysBeforeDeparture,
                                           hoursBeforeDeparture,paths["grib_path"],paths["netcdf_path"])

                # set the number of scenario files to create depending on the type of time windows to be analysed,
                # where the default is 4 consisting of 1min,60min the probabilistic and the deterministic. If the
                # probabilistic and deterministic time windows are equal create only the deterministic scenario.

                twWidths = { '01': 1,
                             '15': 15,
                             '60': 60,
                             'deterministic':  int(scenario.tw_deterministic)}

                if twWidths["deterministic"] != int(scenario.tw_probabilistic):
                    twWidths['probabilistic'] = int(scenario.tw_probabilistic)

                departureDelay = [0,10,15,20,30]

                for key in twWidths:
                    for delay in  departureDelay:
                        scnfilename = ".".join(["_".join([key,scenario.acid,
                                                         scenario.date_start.strftime("%Y%m%d"),
                                                         str(delay),
                                                         timeAnalysis,str(stepEnd)]),
                                                         'scn'])

                        with open(os.path.join(currentScndir,scnfilename),"w") \
                                as scnfile:

                            scnfile.write(scenario.initialise_simulation(delay))
                            scnfile.write(scenario.cre(cascr))
                            scnfile.write(scenario.defwpt_command())
                            scnfile.write(scenario.addwpt_command())
                            scnfile.write(scenario.rta_commands(key,afms_mode["wp_frequency"],delay))
                            scnfile.write("0:00:00.00>TW {} ".format(scenario.acid) + str(twWidths[key]*60) + "\n")
                            scnfile.write("0:00:00.00>AFMS {} ".format(scenario.acid) + " ON\n")
                            scnfile.write("0:00:00.00>CRELOG WINDLOG 1.0\n")
                            scnfile.write("0:00:00.00>WINDLOG ADD id,lat,lon,alt,gs,tas,cas,trk,hdg,traf.wind.current_ensemble\n")
                            scnfile.write("0:00:00.00>WINDLOG ON\n")
                            scnfile.write("0:00:00.00>WPTLOG ON\n")
                            scnfile.write(scenario.start_simulation())

