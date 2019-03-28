# from bluesky.navdatabase.loadnavdata import load_navdata
import os
from trajectory.trajectory import trajectories
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
                print("Successfully loaded trajectory: ", name)
        print()


    cre_functions = trajectories.initiate_aircraft()
    dest_functions = trajectories.add_destination()
    addwpt_functions = trajectories.add_all_wpt()


    with open(os.path.join(scn_trajectory_path, 'aggregated_' + str(datetime.datetime.now()) + '.scn'),
              'w') as scenario:
        for i in range(len(cre_functions)):
            scenario.write(cre_functions[i])
            scenario.write(dest_functions[i])
        for function in addwpt_functions['F9.A320.2014-06-25']['addwpt_function']:
            scenario.write(function)
    print("Successfully created scenario file")
    # else:
    #     ValueError("Excepted values are idv/agg")

