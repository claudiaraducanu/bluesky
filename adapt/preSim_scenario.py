import sys,os,logging,datetime
import numpy  as np
import pandas as pd
from scripts import adaptsettings
from scripts import ddr2scn
import  bluesky.traffic.performance.bada.coeff_bada as coefficient


if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    print()
    print("Initialising BlueSky scenario fil1es and retrieving wind data for the trajectories ... ")

    """ load the default settings for the preSimulation BlueSky ( paths where data is stored and where to
    store it after the simulation is run"""
    config = adaptsettings.init()

    paths           = config[config.sections()[0]]
    afms_mode       = config[config.sections()[1]]

    """ Time Window length"""

    tw_length = []

    inputLength = input("Enter the time window length in minutes (e.g. 1 4 6 ): ")
    print()

    # convert the input from str to int
    if len(inputLength):
        inputLength = inputLength.split()
        widths = np.array([int(day) for idx, day in enumerate(inputLength)])
    else:
        widths = 1

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

    # Create a folder to store the scenario files
    logType = 'wptlog'
    currentScndir = os.path.join(paths["scn_path"],logType.upper(),
                                 datetime.datetime.now().strftime("%Y%m%d"))

    if not os.path.isdir(currentScndir):
        print()
        print('No {} directory in {} found'.format(logType.upper() + "/" +datetime.datetime.now().strftime("Y%m%d"),
                                                   paths["scn_path"]))
        os.makedirs(currentScndir)
        print('A default version will be generated,please do not change')
        print()

    """ Loop through the DDR trajectories to create scn files"""

    coefficient.init(bada_path=paths["bada_path"])

    for root,dirs,files in os.walk(paths["ddr_path"]):

        for file in files:
            if file.endswith(".csv"):

                print("trajectory >>>", os.path.splitext(file)[0])
                scenario = ddr2scn.parseDDR(os.path.join(root,file))

                scenario.ac_type  = trajectory_list.loc[scenario.acid]["NAN"]["ac_type"]
                syn, coeff = coefficient.getCoefficients(scenario.ac_type)

                if syn:
                    cascr = coeff.CAScr2[0]
                    mcr   = coeff.Mcr[0]

                    scenario.tw_deterministic   = trajectory_list.loc[scenario.acid]["deterministic"]['TW']
                    scenario.tw_probabilistic   = trajectory_list.loc[scenario.acid]["probabilistic"]['TW']

                    # set the number of scenario files to create depending on the type of time windows to be analysed,
                    # where the default is 4 consisting of 1min,60min the probabilistic and the deterministic. If the
                    # probabilistic and deterministic time windows are equal create only the deterministic scenario.

                    for width in widths:

                    # define the way-points that have an RTA constraint. Start out with the first way-point
                    # such that the AFMS is activated and then continue such that there is a waypoint
                    # with an RTA at least wp_frequency seconds (set in adaptsettings.cfg) away from the last
                    # waypoint with an RTA.

                        rtaWpts = []  # list of way-points that have an RTA constraint
                        currentwp = 0  # current way-point

                        # as long as there are way-points
                        while currentwp < scenario.data.index[-1]:

                            # calculate the number of seconds from current way-point to all the other way-points left in
                            # the trajectory
                            wptimedelta = (scenario.data['time_over'][currentwp + 1:] - \
                                           scenario.data['time_over'][currentwp]).dt.total_seconds()

                            # store the first waypoint that is at least wp_frequency away from the current way-point, if
                            # no waypoint is wp_frequency away it means that you are near the end of the trajectory
                            # so just store the last waypoint in the trajectory

                            if wptimedelta[wptimedelta > int(afms_mode["wp_frequency"])].size:
                                currentwp = wptimedelta[wptimedelta > int(afms_mode["wp_frequency"])].index[0]
                            else:
                                currentwp = scenario.data.index[-1]

                            rtaWpts.append(currentwp)

                        scnfilename = ".".join(["_".join([str(width),
                                                         scenario.acid,
                                                         scenario.date_start.strftime("%Y%m%d")]),
                                                         'scn'])

                        print("              ","scnfile >>> {} ".format(scnfilename))

                        with open(os.path.join(currentScndir,scnfilename),"w") \
                                as scnfile:

                            scnfile.write(scenario.initialise_simulation())
                            scnfile.write(scenario.cre(mcr,cascr))
                            scnfile.write(scenario.defwpt_command())
                            scnfile.write(scenario.addwpt_command(with_spd=False))
                            scnfile.write(scenario.rta_commands(rtaWpts))
                            scnfile.write(scenario.tw_command(width))
                            scnfile.write(scenario.afms_command())
                            scnfile.write(scenario.start_log(log_type=logType))
                            scnfile.write(scenario.start_simulation())


