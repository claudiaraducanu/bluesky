import sys,os,logging
import numpy
from scripts import adaptsettings
from scripts.wind import retrieveWind

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

    print()
    print("Initialising BlueSky scenario files and retrieving wind data for the trajectories ... ")

    """ load the default settings for the preSimulation BlueSky ( paths where data is stored and where to
    store it after the simulation is run"""
    paths = adaptsettings.init()

    """ select the number of days before departure to retrieve wind from """
    # the default number of days before departure is none

    daysBeforeDeparture = []
    interval            = 6                # ECMWF interval of forecast analysis

    inputDays = input("Enter a list of days before departure separated by a space (e.g 0 1 4 6 ): ")
    print()

    # convert the input from str to int
    if len(inputDays):
        inputDays = inputDays.split()
        daysBeforeDeparture = [day for idx, day in enumerate(inputDays)]

    hoursBeforeDeparture = daysBeforeDeparture * 24

    """ """




    # twWidth = input("Select type of time window to initiate scenario file\n"
    #                 "Options available are none, 0, 1, 5, 10, 15 or 60 minutes: ")
    #
    # print("_______________________________________________________________")
    # logType = input("Select type of logger to initiate scenario file\n"
    #                 "Options available are wpt/wind: ")
    #
    # if logType not in ['wptlog', 'windlog']:
    #     logType = 'wptlog'
    #
    # if isinstance(twWidth, str) and len(twWidth) > 0:
    #
    #     if int(twWidth) == 0:
    #         twWidthName = "RTA"
    #     else:
    #         twWidthName = "TW" + twWidth
    #     twWidth = int(twWidth)
    #
    # else:
    #     twWidth = None
    #     twWidthName = twWidth
    # # Create target Directory if don't exist
    #
    #
    # """ wind retrieval for the trajectories"""
    #
    # print()
    # print('retrieving wind file')
    # retrieveWind.retrieveWind(paths["ddr_path"],paths["grib_path"],paths["netcdf_path"])
    #
    # ncTargetAnalysis = os.path.join(ncDirPath,target)
    # grib2netcdf(ncTargetAnalysis, grbTargetAnalysis)
