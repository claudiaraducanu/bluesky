# from bluesky.navdatabase.loadnavdata import load_navdata
import os
from trajectory.ddr2scn import trajectories
import datetime

if __name__ == "__main__":

    ddr2_trajectory_path = os.path.join(os.getcwd(), "data", "ddr")  # Directory with DDR2 trajectory data
    # Where to store trajectories converted to scenario file
    scn_trajectory_path = os.path.join(os.getcwd(), "scenario", "trajectories")  # Directory with DDR2 trajectory data

    trajectories = trajectories()

    # Find all files containing a trajectory
    for root, dirs, files in os.walk(ddr2_trajectory_path):
        for name in files:
            if not name.startswith('.'):
                trajectories.from_csv(os.path.join(root, name))
                print("Succesfully loaded trajectory: ", name)

    trajectories.cre_command()
    trajectories.dest_command()
    trajectories.addwpt_command()

    for key in trajectories.scn:

        with open(os.path.join(scn_trajectory_path, key + '_' + str(datetime.datetime.now()) + '.scn'),
                  'w') as scenario:
            scenario.write('0:00:00.00>HOLD\n')
            scenario.write(trajectories.scn[key]['cre_function'])
            scenario.write(trajectories.scn[key]['dest_function'])
            for function in trajectories.scn[key]['addwpt_functions']:
                scenario.write(function)
            scenario.write("0:00:00.00>" + trajectories.key_to_dict(key)['acid'] + " VNAV ON\n")
            scenario.write("0:00:00.00>LOG ON\n0:00:00.00>OP")