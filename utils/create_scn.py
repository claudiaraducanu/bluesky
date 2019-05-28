import datetime
import sys
import os
# Add to path the current working directory of process, which means this
# script can be run from the same directory as BlueSky.py
# Print current working directory
print("Current working directory : %s" % os.getcwd()) # make sure its BlueSky main
sys.path.insert(0, os.getcwd())
from utils.datTools import ddrToScn, grib2wind
from netCDF4 import Dataset

if __name__ == "__main__":

    ddr_dirName = os.path.join(os.getcwd(), "data", "ddr")
    scn_dirName = os.path.join(os.getcwd(), "scenario", "trajectories",datetime.datetime.now().strftime("%d-%m-%Y"))


    # Create target Directory if don't exist
    if not os.path.exists(scn_dirName):
        os.mkdir(scn_dirName)
        print("Directory ", scn_dirName, " Created ")
    else:
        print("Directory ", scn_dirName, " already exists")

    wind = grib2wind.fetchWind()

    for root, dirs, files in os.walk(ddr_dirName):
        for name in files:
            if not name.startswith('.'):
                # into the trajectories object as a data frame.
                fpath = os.path.join(ddr_dirName, name)
                print("Loading trajectory of flight ", os.path.splitext(name)[0], "...")
                scenario = ddrToScn.FlightPlan(fpath,cruise=True)

                if scenario.date.hour <= 12.0:
                    times = [0,12]
                    input_file = []

                    # TODO include for time when hour is after midday
                    for time in times:
                        input_file.append(wind.fetch_grib_from_ecmwf(scenario.date.year,
                                               scenario.date.month,
                                               scenario.date.day,
                                               time))
                    print("________________________________\n")
                    merge_out_file = os.path.join(wind.gribdatadir,"ecmwf_pl_%04d-%02d-%02d_00-12.grb" % (scenario.date.year,
                                               scenario.date.month, scenario.date.day))
                    if not os.path.exists(merge_out_file):
                        wind.merge(input_file,merge_out_file)
                        print("Merged %s \n%s" % (input_file[0],input_file[1]),"\ninto\n",merge_out_file)
                        print("________________________________\n")

                    wind.grib2netcdf(merge_out_file)

                with open(os.path.join(scn_dirName, scenario.acid + "_" +
                                                    datetime.datetime.now().strftime("%H-%M-%S")  + '.scn'),"w") \
                        as scnfile:
                    scnfile.write(scenario.initialise_simulation())
                    scnfile.write(scenario.defwpt_command())
                    scnfile.write(scenario.addwpt_command())
                    scnfile.write(scenario.start_log(log_type='periodic'))
                    scnfile.write(scenario.start_log(log_type='waypoint'))
                    scnfile.write(scenario.get_route())
                    scnfile.write(scenario.start_simulation())
