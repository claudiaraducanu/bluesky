"""
Wind ensemble model spread plots
=========================================================================
This module extracts the wind residuals from the mean wind of a perturbed
forecast from the flight simulations obtained using BlueSky, where the
residual is described by the function:

    * res_i = w - w_i , where i = {1,..,50}

There are 3 types of wind residuals considered.
    * gs - tas
    * gs_north - tas_north
    * gs_east - tas_east
"""

import numpy as np
import matplotlib.pyplot as plt
import pickle
import pandas as pd
import os, logging, datetime, math

##############################################################################################################
""" Function to plot the residual distribution a wind for each day before departure from which 
perturbed forecast exits. """
##############################################################################################################

def wind_residual_histogram(wind,wind_filename):
    logging.info("%s", wind)

    days_before_departure = wind_log.index.unique().levels[0]

    nrows, ncol = 2, 3
    max_density = []

    fig, axes = plt.subplots(nrows, ncol, sharex=True, sharey=True)

    for idx, day in enumerate(days_before_departure):
        row = math.floor(idx / ncol)
        col = idx % ncol
        # generate histogram of the wind type
        axes[row, col].hist(avg_wind_log[wind].loc[day],
                            color='c', edgecolor='k', alpha=0.65, label="%02d" % day)
        max_density.append(np.max(np.histogram(avg_wind_log[wind].loc[day])[0]))
        # plot the average
        axes[row, col].axvline(avg_wind_log[wind].loc[day].mean(), color='r',
                               linestyle='dashed', linewidth=1)
        axes[row, col].grid()
        axes[row, col].legend(prop={'size': 8})

    # Set common labels
    axes[1, 1].set_xlabel(r'gs$_{i}$ - tas$_{i}$' +' [kts]', fontsize=11)
    axes[0, 0].set_ylabel('density', fontsize=11)
    axes[1, 0].set_ylabel('density', fontsize=11)

    # Set title
    axes[0, 1].set_title("Histogram of \n{}".format(wind), fontsize=12, weight="semibold")

    # Set the ticks and ticklabels for all axes
    plt.setp(axes, xticks=np.arange(math.floor(avg_wind_log[wind].min()), math.ceil(avg_wind_log[wind].max()), 5),
             yticks=np.arange(0, math.ceil(max(max_density)) + 1, 2))

    plt.tight_layout()

    # Save the figures in the corresponding directory
    fname = "_".join(["-".join(wind.split(" ")), datetime.datetime.now().strftime("%Y%m%d"),
                      wind_filename]) + ".png"

    plt.savefig(fname=os.path.join("/Users/Claudia/Documents/5-MSc-2/bluesky/adapt/imageFiles", fname), facecolor='w',
                edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=True, bbox_inches=None, pad_inches=0.1,
                frameon=None, metadata=None)

    plt.show()

##############################################################################################################
""" Load pickle file of WINDLOG data and calculate the 3 types of residual wind """
##############################################################################################################

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

filename = os.path.join(os.getcwd(),"outputBlueSky/WINDLOG/adh931_2014-09-09_00/"
                                    "20190618/WINDLOG_None_adh931_2014-09-09_00_20190618.pkl")

wind_filename = "_".join(os.path.splitext(filename.split("/")[-1])[0].split("_")[2:-1])

wind_log = pickle.load(open(filename,'rb'))
# analysis = analysis.set_index([" hours_before_departure"," current_ensemble","# simt"])
ms = 1.943844 # kts of ms

# calculate the TAS in north and east direction
wind_log[" tasnorth"] = wind_log[" tas"] * np.cos(wind_log[" hdg"]*np.pi/180)
wind_log[" taseast"]  = wind_log[" tas"] * np.sin(wind_log[" hdg"]*np.pi/180)

# calculate the wind residuals in north and east direction and just the gs one
wind_log["N wind residuals"] = (wind_log[" gsnorth"] - wind_log[" tasnorth"]) *ms
wind_log["E wind residuals"]  = (wind_log[" gseast"] - wind_log[" taseast"])  *ms
wind_log["wind residuals"] = (wind_log[" gs"] - wind_log[" tas"]) *ms

# calculate the absolute value of the wind residuals
wind_log["absolute N wind residuals"] = (wind_log[" gsnorth"] - wind_log[" tasnorth"]).abs()
wind_log["absolute E wind residuals"]  = (wind_log[" gseast"] - wind_log[" taseast"]).abs()
wind_log["absolute wind residuals"] = (wind_log[" gs"] - wind_log[" tas"]).abs()

# set index as the forecast analysis time and the ensemble
wind_log = wind_log.set_index([" hours_before_departure"," current_ensemble"])

# Get the average value of all remaining columns over the 2 index
avg_wind_log = wind_log.groupby(by=[" hours_before_departure"," current_ensemble"]).mean()

##############################################################################################################
""" Histogram plots for the 3 types the wind residuals and their absolute value. """
##############################################################################################################

winds = ["E wind residuals", "N wind residuals", "wind residuals",
         "absolute E wind residuals", "absolute N wind residuals",
         "absolute wind residuals"]

for wind in winds:
    wind_residual_histogram(wind,wind_filename)

##############################################################################################################
""" wind spread distribution parameters to Excel"""
##############################################################################################################

days_before_departure = wind_log.index.unique().levels[0]

dist_parameters = []

for wind in winds:
    for idx, day in enumerate(days_before_departure):
        dist_parameters.append([wind,day, avg_wind_log[wind].loc[day].mean(),
                                avg_wind_log[wind].loc[day].median(),
                                avg_wind_log[wind].loc[day].min(),
                                avg_wind_log[wind].loc[day].max(),
                                avg_wind_log[wind].loc[day].std()])

dist_parameters = pd.DataFrame(dist_parameters,columns=["residual_type","day_before_departure","mean","median","min","max","std"])

dist_parameters['mean_kts'] = ms*dist_parameters['mean']
dist_parameters['median_kts'] = ms*dist_parameters['median']
dist_parameters['min_kts'] = ms*dist_parameters['min']
dist_parameters['max_kts'] = ms*dist_parameters['max']
dist_parameters['std_kts'] = ms*dist_parameters['std']


# Save the figures in the corresponding directory
wind_file = "_".join(os.path.splitext(filename.split("/")[-1])[0].split("_")[2:-1])
fname = "_".join(["wind", datetime.datetime.now().strftime("%Y%m%d") ,wind_file]) + ".xlsx"

dist_parameters.to_excel(os.path.join("/Users/Claudia/Documents/5-MSc-2/bluesky/adapt/xlsxFiles",fname),
                         sheet_name='Sheet1',
                   na_rep='', float_format="%.03f", columns=None,
                   header=True, index=True, index_label=None,
                   startrow=0, startcol=0, engine=None, merge_cells=True,
                   encoding=None, inf_rep='inf', verbose=True, freeze_panes=None)