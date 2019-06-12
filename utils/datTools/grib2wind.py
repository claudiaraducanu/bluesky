from ecmwfapi import ECMWFDataServer
import subprocess
import os

def merge_gribfile(output,input_file):

    if len(input_file) == 1:
        raise Warning("Unsuccessful merge",
                      "only one grib file provided for merge")
    elif len(input_file) == 2:
        subprocess.call(["grib_copy", input_file[0], input_file[1], output])

    elif len(input_file) == 3:
        subprocess.call(["grib_copy", input_file[0], input_file[1], input_file[2], output])

    else:
        subprocess.call(["grib_copy", input_file[0], input_file[1], input_file[2], input_file[3],output])


def grib2netcdf(grib_fpath):
    """
    Call the ecCodes API function from command line to
    convert grib file to netcdf to use in windiris.py
    :param filename:
    :return:
    """

    # Netcdf output file
    netcdf_fpath = os.path.join(os.path.join(os.getcwd(), "data", 'netcdf'),
                                ".".join([os.path.splitext(grib_fpath)[0].split("/")[-1],"nc"]))

    if not os.path.exists(netcdf_fpath):
        # Grib file to be converted to netcdf
        subprocess.call(["grib_to_netcdf", "-o", netcdf_fpath, grib_fpath])

def tigge_pf_pl_request(date,time,target):
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
        "step": "0",
        "time": time,
        "type": "pf",
        "target": target,
    })

def retrieve_tigge_data(dates,times):

    targets = []
    for date in dates:
        for time in times:

            target = os.path.join(os.getcwd(), "data", 'grib','ecmwf_pl_%s_%s.grb' % (date, time))
            targets.append(target)

            if not os.path.isfile(target):
                tigge_pf_pl_request(date, time, target)
    return targets


