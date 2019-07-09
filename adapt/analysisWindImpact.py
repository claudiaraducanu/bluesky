import pandas as pd
from netCDF4 import num2date

# simulation file that does not have the wind ensembles
# nwSimFile = "adapt/output/WPTLOG_60_ADH931_20140909_00_12_20190709_10-40-52.log" # speed change required difference 1.0 m/s
nwSimFile   = "adapt/output/WPTLOG_60_ADH931_20140909_00_12_20190709_11-34-04.log"  # speed change required difference .5 m/s
# load the wind file into a dataframe
read_file = pd.read_csv(nwSimFile, header=None, skiprows=8)

# add the name of the columns
columnNames        = ["simt", "acid", "actype", "lat", "lon", "alt", 'tas', "cas", "gs", "fuel_mass","mass"]  # logged data
read_file.columns = columnNames

# determine the arrival time at the last way-point
start_time   = "2014-09-09 05:12:46"
arrival_time = num2date(read_file.simt.iloc[-1], units='seconds since {}'.
                        format(start_time),
                        calendar='gregorian')
