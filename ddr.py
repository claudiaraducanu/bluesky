"""
This module converts the DDR2 files to Bluesky scenario file format.

Created by: Claudia Raducanu
Date: 5.03.2019
"""
import os
from trajectory.ddr2scn import trajectories
import datetime

if __name__ == "__main__":

    log_type = input('Select the type of logger to use \n'
                   'standard/conditional: ') or "standard"

    ddr2_trajectory_path = os.path.join(os.getcwd(), "data", "ddr")  # Directory with DDR2 trajectory data
    # Where to store trajectories converted to scenario file
    scn_trajectory_path = os.path.join(os.getcwd(), "scenario", "trajectories")  # Directory with DDR2 trajectory data

    trajectories = trajectories()

    # Find all files containing a trajectory
    for root, dirs, files in os.walk(ddr2_trajectory_path):
        for name in files:
            if not name.startswith('.'):
                trajectories.from_csv(os.path.join(root, name)) # import all files in the trajectory
                # into the trajectories object as a data frame.
                print("Succesfully loaded trajectory: ", name)

    # Generate BlueSky commands for each aircraft
    trajectories.cre_command()
    trajectories.dest_command()
    trajectories.orig_command()
    trajectories.addwpt_command()

    # Create the scenario files for each aircraft by appending the commands
    for key in trajectories.scn:

        with open(os.path.join(scn_trajectory_path, key + '_' + log_type + '_' +
                                                    str(datetime.datetime.now()) + '.scn'),
                  'w') as scenario: # open the file

            scenario.write('0:00:00.00>HOLD\n')
            scenario.write('0:00:00.00>DATE \n')
            scenario.write(trajectories.scn[key]['cre_function'])
            scenario.write(trajectories.scn[key]['orig_function'])
            scenario.write(trajectories.scn[key]['dest_function'])
            for function in trajectories.scn[key]['addwpt_functions']:
                scenario.write(function)
            scenario.write("0:00:00.00>" + trajectories.key_to_dict(key)['acid'] + " VNAV ON\n")
            # Select type of logger to use
            if log_type == "standard":
                scenario.write("0:00:00.00>PLUGINS REMOVE FUELLOG \n"
                               "0:00:00.00>CRELOG STANDARD 0.1 \n"
                               "0:00:00.00>STANDARD ADD id,lat,lon,alt,traf.perf.mass,traf.ap.route[0].iactwp\n"
                               "0:00:00.00>STANDARD ON\n")
            elif log_type == "conditional":
                scenario.write("0:00:00.00>PLUGINS LOAD FUELLOG \n"
                               "0:00:00.00>FLOG ON\n")
            else:
                raise ValueError("Unknown logger type.")
            scenario.write("0:00:00.00>OP")