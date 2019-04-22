"""
This module plots the flight parameters logged

Created by: Claudia Raducanu
Date: 20.04.2019
"""

import os
import pandas as pd
import pickle as pkl
import matplotlib.pyplot as plt
from datetime import datetime

if __name__ == "__main__":

    outdir = os.path.join(os.getcwd(), 'output')
    plot_outdir = os.path.join(os.getcwd(), 'utils','Data processing','plots')

    # Find all files containing a trajectory
    for root, dirs, files in os.walk(outdir):
        for name in files:
            print(name)
            if not name.startswith('.') and name.endswith('.log'):

                data = pd.read_csv(os.path.join(outdir, name))
                print("Successfully loaded trajectory from log file: ", name)

            elif not name.startswith('.') and name.endswith('.pkl'):

                with open(os.path.join(outdir, name),"rb") as file:
                    data = pkl.load(file)
                print("Successfully loaded trajectory from pickle file: \n", name)
            else:
                print("No data loaded.")
                # pass

        # process name
        split_name = name.split('_')

        name_components = {'log_name':split_name[0],
                           'flight_id':split_name[1],
                           'ac_type':split_name[2],
                           'flight_date:':split_name[3],
                           'logging_type':split_name[4],
                           'creation_time':split_name[5],
                           'simulation_date':split_name[6],
                           'simulation_time':split_name[7].split('.')[0]}


        # Plotting

        fig, ax = plt.subplots(2, 2) # create full grid of subplots in a single line

        # First subplot
        ax[0,0].set_ylabel('$m$',fontsize=12)
        data.plot(kind='line',x='Simulation time [s] ',y=['Altitude [m] '],
                  grid=True,color='red',ax=ax[0,0],legend=False)
        ax[0,0].set_title("Altitude")

        # Second subplot
        ax[0,1].set_ylabel(r'$\frac{m}{s}$',fontsize=12)
        ax[0,1].set_title("Speed")
        data.plot(kind='line',x='Simulation time [s] ',y=['Ground Speed [m/s] '],
                  grid=True,color='red',ax=ax[0,1])
        data.plot(kind='line',x='Simulation time [s] ',y=['CAS [m/s] '],
                  grid=True,color='blue',ax=ax[0,1])

        # Third subplot
        ax[1,0].set_ylabel('$kg$',fontsize=12)
        ax[1,0].set_title("Mass")
        data.plot(kind='line',x='Simulation time [s] ',y=['Actual Mass [kg] '],grid=True,color='red',ax=ax[1,0],legend=False)

        # 4th subplot
        ax[1,1].set_ylabel('$kg$',fontsize=12)
        ax[1,1].set_title("Fuel Consumed")
        data.plot(kind='line',x='Simulation time [s] ',y=['Initial Mass - Actual Mass [kg]'],grid=True,
                  color='blue',ax=ax[1,1],legend=False)

        # Make room for the ridiculously large title.
        fig.tight_layout()
        plt.suptitle("Flight Parameters " + name_components['flight_id'])

        timestamp = datetime.now().strftime('%Y%m%d_%H-%M-%S')
        f_name = os.path.join(plot_outdir,"%s_%s_%s_%s.eps" % ("flight_param",name_components['flight_id'],
                                                         name_components["log_name"],timestamp))

        plt.savefig(f_name, dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None, metadata=None)