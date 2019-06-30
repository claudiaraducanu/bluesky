import os
import numpy as np
import datetime
from ecmwfapi import ECMWFDataServer
import subprocess

def grib2netcdf(ncFilePath,grbFilePath):
    """
    Call the ecCodes API function from command line to
    convert grib file to netcdf to use in windiris.py
    :param filename:
    :return:
    """
    if not os.path.exists(ncFilePath):
        # Grib file to be converted to netcdf
        subprocess.call(["grib_to_netcdf","-o",ncFilePath, grbFilePath])

def tigge_pf_pl_request(date,time,step,target):
    '''
       A TIGGE request for perturbed forecast, pressure level, ECMWF Center.
       Please note that a subset of the available data is requested below.
       Change the keywords below to adapt it to your needs. (ie to add more parameters, or numbers etc)
    '''

    ECMWFDataServer().retrieve({
        "class": "ti",
        "dataset": "tigge",
        "date": date,
        "expver": "prod",
        "grid": "0.5/0.5",
        "levelist": "200/250/300/500/700/850/925/1000",
        # type of level
        "levtype": "pl",
        # ensemble number
        "number": "1/2/3/4/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/20"
                  "/21/22/23/24/25/26/27/28/29/30/31/32/33/34/35/36/37"
                  "/38/39/40/41/42/43/44/45/46/47/48/49/50",
        "origin": "ecmf",
        "param": "131/132",
        "step": step,
        "time": time,
        "type": "pf",
        "target": target,
    })

def downloadWind(scenario,daysBeforeDeparture,hoursBeforeDeparture,grbDirPath,ncDirPath):

    stepStart           = 0
    interval            = 6                # ECMWF interval of forecast analysis

    dateDeparture  = scenario.date_start.date()
    tDelta = daysBeforeDeparture * datetime.timedelta(days=1)
    datesBeforeDeparture = dateDeparture - tDelta

    if scenario.date_start.hour >= 12:
        timeAnalysis = "12"
    else:
        timeAnalysis = "00"

    if scenario.date_start.hour < 12 <= scenario.date_end.hour:
        stepEnd = 18
    else:
        stepEnd = 12

    steps = list(range(stepStart,stepEnd+1,interval))

    forecastSteps = [steps] * hoursBeforeDeparture.size
    forecastSteps = np.array(forecastSteps).reshape(hoursBeforeDeparture.size, len(steps))
    forecastSteps = forecastSteps + np.vstack(hoursBeforeDeparture)

    for idx,date in enumerate(datesBeforeDeparture):

        dateAnalysis = datesBeforeDeparture[idx].strftime("%Y-%m-%d")
        stepsAnalysis  = "/".join(forecastSteps[idx].astype(str).tolist())

        target = 'ecmwf_pl_%s_%s_%s.grb' % (dateDeparture.strftime("%Y%m%d"), timeAnalysis,
                                            "-".join(forecastSteps[idx].astype(str).tolist()))
        grbTargetAnalysis = os.path.join(grbDirPath,target)

        if not os.path.isfile(grbTargetAnalysis):
            tigge_pf_pl_request(dateAnalysis, timeAnalysis, stepsAnalysis, grbTargetAnalysis)

        ncTargetAnalysis = os.path.join(ncDirPath, ".".join([os.path.splitext(target)[0],"nc"]))

        if not os.path.isfile(ncTargetAnalysis):
            grib2netcdf(ncTargetAnalysis, grbTargetAnalysis)

    return timeAnalysis,stepEnd