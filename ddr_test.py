import os
import datetime
from trajectory.trajectory import trajectories

ddr2_trajectory_path = os.path.join(os.getcwd(),"data", "ddr") # Directory with DDR2 trajectory data
# Where to store trajectories converted to scenario file
scn_trajectory_path = os.path.join(os.getcwd(),"scenario", "trajectories") # Directory with DDR2 trajectory data

trajectories = trajectories()

# Find all files containing a trajectory
for root, dirs, files in os.walk(ddr2_trajectory_path):
   for name in files:

       if not name.startswith('.'):
           trajectories.from_csv(os.path.join(root, name))
           print("Succesfully loaded trajectory: ",name)
   print()

scn_type = input(' Enter type of scenario file \n options are individual (idv)/ aggregated (agg)): ')


cre_functions = trajectories.initiate_aircraft()
dest_functions = trajectories.add_destination()
addwpt_functions = trajectories.add_all_wpt()



if scn_type == "idv":
    print("hello")
elif scn_type == "agg":

    with open(os.path.join(scn_trajectory_path, 'aggregated_' + str(datetime.datetime.now()), '.scn'), 'w') as scenario:
        for i in range(len(cre_functions)):
            scenario.write(cre_functions[i])
            scenario.write(dest_functions[i])
        for key in trajectories.data:
            for function in addwpt_functions[key]['addwpt_function']:
                print(function)
                scenario.write( function )
else:
    ValueError("Excepted values are idv/agg")


