import os
import numpy as np
import datetime
from ecmwfapi import ECMWFDataServer
import subprocess

def _grib2netcdf(ncFilePath,grbFilePath):
    """
    Call the ecCodes API function from command line to
    convert grib file to netcdf to use in windiris.py
    :param filename:
    :return:
    """
    if not os.path.exists(ncFilePath):
        # Grib file to be converted to netcdf
        subprocess.call(["grib_to_netcdf","-o",ncFilePath, grbFilePath])

def _tigge_pf_pl_request(date,time,step,target):
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


def DownloadWind(date_departure,
                 forecast_analysis_date,
                 forecast_analysis_time,
                 forecast_steps,grbDirPath,ncDirPath):

    forecast_analysis_date  = forecast_analysis_date.strftime("%Y-%m-%d")
    forecast_steps          = "/".join(forecast_steps.astype(int).astype(str).tolist())

    target = 'ecmwf_pl_%s_%s_%s.grb' % (date_departure.strftime("%Y%m%d"),
                                        forecast_analysis_time,
                                        "-".join(forecast_steps.split("/")))

    grb_target = os.path.join(grbDirPath,target)

    if not os.path.isfile(grb_target):
        print(f"Dowloading forecast from {forecast_analysis_date} for {forecast_steps} in the future")
        _tigge_pf_pl_request(forecast_analysis_date,
                             forecast_analysis_time,
                             forecast_steps, grb_target)

    ncTargetAnalysis = os.path.join(ncDirPath, ".".join([os.path.splitext(target)[0],"nc"]))

    if not os.path.isfile(ncTargetAnalysis):
        _grib2netcdf(ncTargetAnalysis, grb_target)
