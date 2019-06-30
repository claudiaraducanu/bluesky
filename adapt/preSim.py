import sys,os,logging,datetime
import numpy  as np
import pandas as pd
from scripts import adaptsettings
from scripts import grib2wind
from scripts import ddr2scn

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    print()
    print("Initialising BlueSky scenario files and retrieving wind data for the trajectories ... ")

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

    """ remon results to get aircraft type and time window"""
    trajectory_list = pd.read_csv(os.path.join(paths["input_path"],"dataResultsRemon.csv"), header=None,skiprows=-1)
    trajectory_list = trajectory_list[trajectory_list.columns[:-11]]
    trajectory_list = trajectory_list.iloc[:-1]

    # set dataframe columns
    col_level1 = pd.Series(trajectory_list.iloc[0]).fillna(method='ffill')
    col_level1[col_level1.isna()] = "NAN"
    col_level2  = pd.Series(trajectory_list.iloc[1]).fillna(method='ffill')

    col = list(zip(col_level1,col_level2))

    # dataframe index is ACID
    trajectory_list         = trajectory_list[2:]
    trajectory_list.columns = pd.MultiIndex.from_tuples(col)
    trajectory_list = trajectory_list.set_index([("NAN","Acid")])
    trajectory_list.set_index(pd.Series([index.split()[0] for index in trajectory_list.index]),inplace=True)

    """ select logtype to initialise the scenario files and create a directory for the data"""

    logType = input("Select type of logger to initiate scenario file\n"    
                    "Options available are wpt/wind: ")
    print()

    if logType not in ['wptlog', 'windlog']:
            logType = 'wptlog'

    currentScndir = os.path.join(paths["scn_path"],logType.upper(),datetime.datetime.now().strftime("%Y%m%d"))
    if not os.path.isdir(currentScndir):
        print()
        print('No {} directory in {} found'.format(logType.upper() + "/" +datetime.datetime.now().strftime("Y%m%d"),
                                                   paths["scn_path"]))
        os.makedirs(os.path.join(paths["scn_path"],logType.upper(),datetime.datetime.now().strftime("%Y%m%d")))
        print('A default version will be generated,please do not change')
        print()

    """ Loop through the DDR trajectories"""
    for root,dirs,files in os.walk(paths["ddr_path"]):

        for file in files:
            if file.endswith(".csv"):

                print("trajectory >>>", os.path.splitext(file)[0])
                scenario = ddr2scn.parseDDR(os.path.join(root,file), cruise=True)
    
                scenario.ac_type            = trajectory_list.loc[scenario.acid]["NAN"]["ac_type"]
                scenario.tw_deterministic   = trajectory_list.loc[scenario.acid]["deterministic"]['TW']
                scenario.tw_probabilistic   = trajectory_list.loc[scenario.acid]["probabilistic"]['TW']

                """Retrieve wind"""
                timeAnalysis,stepEnd = grib2wind.downloadWind(scenario,daysBeforeDeparture,
                                          hoursBeforeDeparture,paths["grib_path"],paths["netcdf_path"])

                twWidths = { '01': 1,
                             '60': 60,
                             'deterministic':  int(scenario.tw_deterministic),
                             'probabilistic':  int(scenario.tw_probabilistic)}

                rtaWpts = [0]
                idx     = 0

                while idx < scenario.data.index[-1]:

                    wptimedelta = (scenario.data['time_over'][idx+1:] - \
                                    scenario.data['time_over'][idx]).dt.total_seconds()
                    if wptimedelta[wptimedelta > int(afms_mode["wp_frequency"])].size:
                        idx = wptimedelta[wptimedelta > int(afms_mode["wp_frequency"])].index[0]
                    else:
                        idx = scenario.data.index[-1]

                    rtaWpts.append(idx)

                for key in twWidths:

                    scnfilename = ".".join(["_".join([key,
                                                     scenario.acid,
                                                     scenario.date_start.strftime("%Y%m%d"),
                                                     timeAnalysis,str(stepEnd)]),
                                                     'scn'])

                    print("              ","scnfile >>> {} ".format(scnfilename))


                    with open(os.path.join(currentScndir,scnfilename),"w") \
                            as scnfile:

                        scnfile.write(scenario.initialise_simulation())
                        scnfile.write(scenario.defwpt_command())
                        scnfile.write(scenario.addwpt_command(with_spd=False))
                        scnfile.write(scenario.rta_command(rtaWpts))
                        scnfile.write(scenario.twSize_command(rtaWpts,twWidths[key]))
                        scnfile.write(scenario.afms_command(rtaWpts,"tw"))
                        scnfile.write(scenario.start_log(log_type=logType))
                        scnfile.write(scenario.start_simulation())

