import datetime
import os
from utils.datTools import ddrToScn

if __name__ == "__main__":

    ddrDirName = os.path.join("data", "ddr")
    scnDirName = os.path.join("scenario", "trajectories", datetime.datetime.now().strftime("%d_%m_%Y"))
    print(scnDirName)
    # Create target Directory if don't exist
    if not os.path.exists(scnDirName):
        os.mkdir('hello')
        print("Directory ", scnDirName, " created ")
    else:
        print('-')

    print("_______________________________________________________________")

    for root, dirs, files in os.walk(ddrDirName):
        for name in files:
            if not name.startswith('.'):


                # into the trajectories object as a data frame.
                fpath = os.path.join(ddrDirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.FlightPlan(fpath,cruise=True)

                with open(os.path.join(scnDirName, scenario.acid + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())
                    scnfile.write(scenario.addwpt_command())
                    scnfile.write(scenario.start_log(log_type='waypoint'))
                    # scnfile.write(scenario.get_route())
                    scnfile.write(scenario.start_simulation())

                print("Done")
                print("_______________________________________________________________")
