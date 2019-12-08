import os,logging,datetime
import fnmatch
import pandas as pd

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    bluesky_scn_path = "/Users/Claudia/Documents/5-MSc-2/bluesky/scenario"
    data_set_path = os.path.join(os.getcwd(),"input", "ddr")
    indv_scn_path  = os.path.join(bluesky_scn_path,"asymmetric",datetime.datetime.now().strftime("%Y%m%d"),"individual")
    traj_scn_path  = os.path.join(bluesky_scn_path,"asymmetric",datetime.datetime.now().strftime("%Y%m%d"),"trajectory")

    if not os.path.isdir(traj_scn_path):
        print()
        print('Directory not found.')
        os.makedirs(traj_scn_path)
        print('A default version will be generated')
        print()

    trajectory_list = pd.read_excel(os.path.join(os.getcwd(),"input", "final.xlsx"))
    trajectory_acid = trajectory_list["acid"]

    """ Loop through the DDR trajectories to create scn files"""

    for t in trajectory_acid:

        files = [ file for file in os.listdir(indv_scn_path) if fnmatch.fnmatch(file,"*{}*.scn".format(t))]

        traj_scn_file = ".".join([t,'scn'])
        traj_scn      = os.path.join(traj_scn_path,traj_scn_file)

        with open(traj_scn, "w") as scnfile:
            scnfile.write("0:00:00.00>HOLD \n")

            batchsim = "0:00:00.00>BATCHSIM " + os.path.join("asymmetric",
                                                             datetime.datetime.now().strftime("%Y%m%d"),"individual") + \
                       "/" + pd.Series(files) + " 1 \n"

            for row in batchsim:
                scnfile.write(row)

            scnfile.write("0:00:00.00>BATCHSTART")




