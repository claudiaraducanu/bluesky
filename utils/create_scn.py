import datetime
import sys
import os
# Add to path the current working directory of process, which means this
# script can be run from the same directory as BlueSky.py
# Print current working directory
print("Current working directory : %s" % os.getcwd()) # make sure its BlueSky main
sys.path.insert(0, os.getcwd())
from utils.datTools import ddrToScn, grib2wind

if __name__ == "__main__":

    wspd = input("Include speed at waypoint")

    ddr_dirName = os.path.join(os.getcwd(), "data", "ddr")
    grib_dirName = os.path.join(os.getcwd(), "data", "grib")
    scn_dirName = os.path.join(os.getcwd(), "scenario", "trajectories",
                               datetime.datetime.now().strftime("%d-%m-%Y"))


    # Create target Directory if don't exist
    if not os.path.exists(scn_dirName):
        os.mkdir(scn_dirName)
        print("Directory ", scn_dirName, " created ")
    else:
        print("Directory ", scn_dirName, " already exists")

    # Create target for wind data if don't exist
    if not os.path.exists(grib_dirName):
        os.mkdir(grib_dirName)
        print("Directory ", grib_dirName, " created ")
    else:
        print("Directory ", grib_dirName, " already exists")


    print("_______________________________________________________________")

    times = ["00", "12"]

    for root, dirs, files in os.walk(ddr_dirName):
        for name in files:
            if not name.startswith('.'):


                # into the trajectories object as a data frame.
                fpath = os.path.join(ddr_dirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")

                scenario = ddrToScn.FlightPlan(fpath,cruise=True)
                print("End Time ",scenario.date_end.time(),"Start",scenario.date_start.time())

                dates = []

                # Retrieve wind data

                dates.append((scenario.date_start.date().strftime("%Y-%m-%d")))
                dates.append((scenario.date_end.date().strftime("%Y-%m-%d")))

                if scenario.date_start.hour >= 12 or scenario.date_end.hour >= 12:
                    dates.append((scenario.date_start.date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"))

                dates = set(dates)
                targets = grib2wind.retrieve_tigge_data(dates, times) # download corresponding files

                output = os.path.join(grib_dirName, ".".join([os.path.splitext(name)[0], "grb"]))
                if not os.path.isfile(output):
                    grib2wind.merge_gribfile(output, targets) # merge corresponding file

                grib2wind.grib2netcdf(output) # convert to netcdf

                with open(os.path.join(scn_dirName, scenario.acid + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())
                    scnfile.write(scenario.addwpt_command(with_spd=wspd))
                    scnfile.write(scenario.start_log(log_type='waypoint'))
                    # scnfile.write(scenario.get_route())
                    scnfile.write(scenario.start_simulation())

                print("Done")
                print("_______________________________________________________________")
