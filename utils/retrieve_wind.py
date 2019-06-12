import sys
import os
import datetime
# Add to path the current working directory of process, which means this
# script can be run from the same directory as BlueSky.py
# Print current working directory
print("Current working directory : %s" % os.getcwd()) # make sure its BlueSky main
sys.path.insert(0, os.getcwd())
from utils.datTools import ddrToScn, grib2wind

if __name__ == "__main__":

    ddr_dirName   = os.path.join(os.getcwd(), "data", "ddr")
    grib_dirName  = os.path.join(os.getcwd(), "data", "grib")

    times = ["00", "12"]

    for root, dirs, files in os.walk(ddr_dirName):
        for name in files:
            if not name.startswith('.'):

                dates = []
                # into the trajectories object as a data frame.

                fpath = os.path.join(ddr_dirName, name)
                print("_______________________________________________________________")

                print("Getting date of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.FlightPlan(fpath,cruise=True)

                dates.append((scenario.date_start.date().strftime("%Y-%m-%d")))
                dates.append((scenario.date_end.date().strftime("%Y-%m-%d")))

                if scenario.date_start.hour >= 12 or scenario.date_end.hour >= 12:
                    dates.append((scenario.date_start.date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))

                seen = set()
                seen_add = seen.add
                dates = [x for x in dates if not (x in seen or seen_add(x))]

                targets = grib2wind.retrieve_tigge_data(dates,times)

                output = os.path.join(grib_dirName, ".".join([os.path.splitext(name)[0],"grb"]))
                if not os.path.isfile(output):
                    grib2wind.merge_gribfile(output,targets)

                grib2wind.grib2netcdf(output)
