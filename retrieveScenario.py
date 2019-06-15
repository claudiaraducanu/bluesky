import datetime
import os
from utils.datTools import ddrToScn

if __name__ == "__main__":

    ddrDirName = os.path.join("data", "ddr")

    print("_______________________________________________________________")
    twWidth = input("Select type of time window to initiate scenario file\n"
                    "Options available are none, 0, 1, 5, 10, 15 or 60 minutes: ")

    if isinstance(twWidth, str) and len(twWidth) > 0:

        if int(twWidth) == 0:
            scnDirName = os.path.join("scenario", datetime.datetime.now().strftime("%d-%m-%Y"),"rta")
        else:
            scnDirName = os.path.join("scenario", datetime.datetime.now().strftime("%d-%m-%Y"),"tw_{}".format(twWidth))
        twWidth = int(twWidth)

    else:
        twWidth = None
        scnDirName = os.path.join("scenario", datetime.datetime.now().strftime("%d-%m-%Y"),str(twWidth))

    # Create target Directory if don't exist
    if not os.path.exists(scnDirName):
        os.makedirs(scnDirName)
        print("Directory ", scnDirName, " created ")

    print("_______________________________________________________________")

    for root, dirs, files in os.walk(ddrDirName):

        for name in files:
            if not name.startswith('.'):

                # into the trajectories object as a data frame.
                fpath = os.path.join(ddrDirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.FlightPlan(fpath,cruise=True)
                rtaWpts      = [1,scenario.data.index.max()]

                with open(os.path.join(scnDirName, scenario.acid + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())

                    if twWidth is not None:

                        scnfile.write(scenario.addwpt_command())
                        scnfile.write(scenario.rta_command(rtaWpts))

                    scnfile.write(scenario.start_log(log_type='waypoint'))
                    scnfile.write(scenario.start_simulation())

                print("Done")
                print("_______________________________________________________________")
