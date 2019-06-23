import datetime
import os
from adapt.scenarioGeneration import ddrToScn

if __name__ == "__main__":

    root = "/Users/Claudia/Documents/5-MSc-2/bluesky"
    ddrDirName = os.path.join(root,"data", "ddr")

    print("_______________________________________________________________")
    twWidth = input("Select type of time window to initiate scenario file\n"
                    "Options available are none, 0, 1, 5, 10, 15 or 60 minutes: ")

    print("_______________________________________________________________")
    logType = input("Select type of logger to initiate scenario file\n"
                    "Options available are wpt/wind: ")

    if logType not in ['wptlog', 'windlog']:
        logType = 'wptlog'

    if isinstance(twWidth, str) and len(twWidth) > 0:

        if int(twWidth) == 0:
            twWidthName = "RTA"
        else:
            twWidthName = "TW" + twWidth
        twWidth = int(twWidth)

    else:
        twWidth = None
        twWidthName = twWidth
    # Create target Directory if don't exist

    scnDirName = os.path.join(root,"scenario", datetime.datetime.now().strftime("%d-%m-%Y"),logType)

    if not os.path.exists(scnDirName):
        os.makedirs(scnDirName)
        print("Directory ", scnDirName, " created ")

    for root, dirs, files in os.walk(ddrDirName):

        for name in files:
            if not name.startswith('.'):

                # into the trajectories object as a data frame.
                fpath = os.path.join(ddrDirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.parseDDR(fpath, cruise=True)

                # TODO : make more flexible
                rtaWpts      = [1,14,scenario.data.index.max()]

                if scenario.date_start.hour >= 12:
                    timeAnalysis = "12"
                else:
                    timeAnalysis = "00"

                with open(os.path.join(scnDirName, str(twWidthName) + "_" + scenario.acid + "_" +
                                                   scenario.date_start.strftime("%Y-%m-%d") + "_" +
                                                   timeAnalysis + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())

                    if twWidth is not None:

                        scnfile.write(scenario.addwpt_command(with_spd=False))
                        scnfile.write(scenario.rta_command(rtaWpts))

                        if twWidth > 0:
                            scnfile.write(scenario.twSize_command(rtaWpts,twWidth))
                            scnfile.write(scenario.afms_command(rtaWpts,"tw"))

                        else:
                            scnfile.write(scenario.afms_command(rtaWpts,"rta"))

                    else:
                        scnfile.write(scenario.addwpt_command(with_spd=True))

                    scnfile.write(scenario.start_log(log_type=logType))
                    scnfile.write(scenario.start_simulation())

                print("Done")
                print("_______________________________________________________________")
