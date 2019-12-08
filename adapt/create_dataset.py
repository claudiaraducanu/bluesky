import pandas as pd
import numpy as np
import os
import shutil

if __name__ == "__main__":

    trajectories = np.array(
        pd.read_excel(os.path.join(os.getcwd(),"input","symmetric.xlsx")).acid)

    a_ddr_path  = os.path.join(os.getcwd(),"input","ddr_symmetric")
    # o_ddr_path  = os.path.join(os.getcwd(),"input","ddr_original")
    ddr_path    = os.path.join(os.getcwd(),"input","ddr2")

    afiles       = [os.path.join(a_ddr_path,f) for f in os.listdir(a_ddr_path) if f.split(".")[0] in trajectories]
    # ofiles       = [os.path.join(o_ddr_path,f) for f in os.listdir(o_ddr_path) if f.split(".")[0] in trajectories]

    for f in afiles:
        shutil.copy(f,ddr_path)
