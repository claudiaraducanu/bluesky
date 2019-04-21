import csv
import os
import pandas as pd
import sys
import matplotlib.pyplot as plt
# import seaborn as sns


outdir = os.path.join(os.getcwd(), 'output')
print(outdir)

# Find all files containing a trajectory
for root, dirs, files in os.walk(outdir):
    for name in files:
        if not name.startswith('.'):

            data = pd.read_csv(os.path.join(outdir, name))
            print("Succesfully loaded trajectory: ", name)

            fuel_used = data

            ax = plt.gca()
            ax.set_title("Aircraft altitude")
            data.plot(kind='line',x='Simulation time [s] ',y=['Altitude [m] '],
                      grid=True,color='red',ax=ax)
            plt.show()