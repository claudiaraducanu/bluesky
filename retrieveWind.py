import os
import numpy as np
import datetime
from utils.datTools import ddrToScn, grib2wind

if __name__ == "__main__":

    #########################################################################################
    """ Initialise """
    #########################################################################################

    print("Wind retrieval function for ADAPT simulations")
    print("____________________________________________________")

    grbDirPath  = os.path.join("data", "grib")
    if not os.path.exists(grbDirPath):
        os.mkdir(grbDirPath)
        print("Create directory ", grbDirPath, " ... ")

    ncDirPath  = os.path.join("data", "netcdf")
    if not os.path.exists(ncDirPath):
        os.mkdir(ncDirPath)
        print("Create directory ", ncDirPath, " ... ")

    #########################################################################################
    """ DDR trajectory folder setup"""
    #########################################################################################

    ddrDirName = input("Default directory for DDR data is the bluesky/data/ddr\n"
                       "If required, provide the subdirectory of default\n"
                       "that contains the DDR trajectory data: ")

    if len(ddrDirName) > 0:
        # only subdirectories of the default directory are accepted.
        ddrDirPath = os.path.join("data", "ddr", ddrDirName)
    else:
        ddrDirPath = os.path.join("data", "ddr")

    #########################################################################################
    """ Days before flight"""
    #########################################################################################

    # the default number of days before departure is none
    daysBeforeDeparture = [0]

    stepStart = 0
    interval = 6

    input_days = input("Enter a list of days before departure separated by a space (e.g 1 4 6 ): ")

    if len(input_days) > 0:
        if len(input_days) > 1:
            input_days = input_days.split(" ")

        daysBeforeDeparture = np.array(daysBeforeDeparture + list(map(int, input_days)))

    hoursBeforeDeparture = daysBeforeDeparture * 24

    #########################################################################################
    """ Files setup"""
    #########################################################################################

    for root,dir,files in os.walk(ddrDirPath):
        for f in files:
            if not f.startswith('.'):
            # into the trajectories object as a data frame.
                filePath = os.path.join(root, f)

                print("_______________________________________________________________")
                print("Trajectory ", os.path.splitext(f)[0], "...")
                scenario = ddrToScn.FlightPlan(filePath,cruise=True)

                # dates from which to retrieve wind parameter strftime("%Y-%m-%d")
                dateDeparture  = scenario.date_start.date()
                tDelta = daysBeforeDeparture * datetime.timedelta(days=1)
                datesBeforeDeparture = dateDeparture - tDelta

                if scenario.date_start.hour >= 12:
                    timeAnalysis = "12"
                else:
                    timeAnalysis = "00"

                if scenario.date_start.hour < 12 <= scenario.date_end.hour:
                    stepEnd   = 18
                else:
                    stepEnd = 12

                steps = list(range(stepStart,stepEnd+1,interval))
                forecastSteps = [steps for idx in range(daysBeforeDeparture.size)]
                forecastSteps = np.array(forecastSteps).reshape(daysBeforeDeparture.size, len(steps))
                forecastSteps = forecastSteps + np.vstack(hoursBeforeDeparture)

                for idx,date in enumerate(datesBeforeDeparture):

                    dateAnalysis = datesBeforeDeparture[idx].strftime("%Y-%m-%d")
                    stepsAnalysis  = "/".join(forecastSteps[idx].astype(str).tolist())

                    target = 'ecmwf_pl_%s_%s_%s.grb' % (dateDeparture.strftime("%Y-%m-%d"), timeAnalysis,
                                                        "-".join(forecastSteps[idx].astype(str).tolist()))
                    grbTargetAnalysis = os.path.join(grbDirPath,target)

                    if not os.path.isfile(grbTargetAnalysis):
                        grib2wind.tigge_pf_pl_request(dateAnalysis, timeAnalysis, stepsAnalysis, grbTargetAnalysis)

                    ncTargetAnalysis = os.path.join(ncDirPath,target)
                    grib2wind.grib2netcdf(ncTargetAnalysis,grbTargetAnalysis)
