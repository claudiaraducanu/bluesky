import datetime
import sys
import os
# Add to path the current working directory of process, which means this
# script can be run from the same directory as BlueSky.py
# Print current working directory
print("Current working directory : %s" % os.getcwd()) # make sure its BlueSky main
sys.path.insert(0, os.getcwd())
from utils.datTools import ddrToScn

if __name__ == "__main__":

    ddr_dirName = os.path.join(os.getcwd(), "data", "ddr")
    scn_dirName = os.path.join(os.getcwd(), "scenario", "trajectories",datetime.datetime.now().strftime("%d-%m-%Y"))

    # Create target Directory if don't exist
    if not os.path.exists(scn_dirName):
        os.mkdir(scn_dirName)
        print("Directory ", scn_dirName, " Created ")
    else:
        print("Directory ", scn_dirName, " already exists")

    for root, dirs, files in os.walk(ddr_dirName):
        for name in files:
            if not name.startswith('.'):
                # into the trajectories object as a data frame.
                fpath = os.path.join(ddr_dirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.FlightPlan(fpath,cruise=True)

                with open(os.path.join(scn_dirName, scenario.acid + "_" +
                                                    datetime.datetime.now().strftime("%H-%M-%S")  + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())
                    scnfile.write(scenario.addwpt_command())
                    scnfile.write(scenario.start_simulation(log_type='periodic'))
