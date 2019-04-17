import os
import datetime
from trajectory.ddr2scn import trajectories

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





# if scn_type == "idv":
#     for key in trajectories.scn:
#         with open(os.path.join(scn_trajectory_path, key + '_' + str(datetime.datetime.now()) + '.scn'),
#                   'w') as scenario:
#                 scenario.write(trajectories.scn[key]['cre_function'])
#                 scenario.write(trajectories.scn[key]['dest_function'])
#                 for function in trajectories.scn[key]['addwpt_functions']['addwpt_function']:
#                     print(function)
#                     scenario.write(function)
# elif scn_type == "agg":
#     with open(os.path.join(scn_trajectory_path, 'aggregated_' + str(datetime.datetime.now()) + '.scn'), 'w') as scenario:
#         for key in trajectories.scn:
#             scenario.write(trajectories.scn[key]['cre_function'])
#             scenario.write(trajectories.scn[key]['dest_function'])
#             for function in trajectories.scn[key]['addwpt_functions']['addwpt_function']:
#                 scenario.write(function)
# else:
#     ValueError("Excepted values are idv/agg")


