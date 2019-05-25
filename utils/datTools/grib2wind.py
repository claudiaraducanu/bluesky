import sys
import os
# Add to path the current working directory of process, which means this
# script can be run from the same directory as BlueSky.py
# Print current working directory
# print("Current working directory : %s" % os.getcwd()) # make sure its BlueSky main
# sys.path.insert(0, os.getcwd())
from ecmwfapi import ECMWFDataServer
import subprocess
import os

class fetchWind():

    def __init__(self):
        # Add new data directories from which to retrieve files
        self.netcdfdatadir = os.path.join(os.getcwd(), "data", 'netcdf')
        self.gribdatadir = os.path.join(os.getcwd(), "data", 'grib')
        # ECMWF server
        self.server = ECMWFDataServer()


    def _grib2netcdf(self,fpath,filename):
        """
        Call the ecCodes API function from command line to
        convert grib file to netcdf to use in windiris.py
        :param filename:
        :return:
        """

        # Netcdf output file

        netcdf_filename = os.path.join(self.netcdfdatadir,"%s.nc" %filename)
        print(netcdf_filename)
        if not os.path.exists(netcdf_filename):

            # Grib file to be converted to netcdf
            print(fpath)
            subprocess.call(["grib_to_netcdf", "-o",
                            netcdf_filename,
                            fpath])
            print("Converted .grb to .nc .")


    def _tigge_pf_pl_request(self,date, target):
        '''
           A TIGGE request for perturbed forecast, pressure level, ECMWF Center.
           Please note that a subset of the available data is requested below.
           Change the keywords below to adapt it to your needs. (ie to add more parameters, or numbers etc)
        '''
        self.server.retrieve({
            "class": "ti",
            "dataset": "tigge",
            "date": "%s" % date,
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
            "time": "00:00:00/12:00:00",
            "type": "pf",
            "target": "%s" % target,
        })


    def fetch_grib_from_ecmwf(self,year, month, day):
        """
        Fetch from the TIGGE dataset propabilistic forecasts
        ( TYPE: perturbed forecast,  LEVEL of TYPE: pressure levels)
        using the MARS interface.
        :param year:
        :param month:
        :param day:
        :param hour:
        :return:
        """

        grib_datadir = os.path.join(os.getcwd(),self.gribdatadir)
        # Check if grib data directory exists, such that .grib files can be saved
        if not os.path.exists(grib_datadir):
            os.makedirs(grib_datadir)

        # date from which to retrive perturbed wind forecast
        ymd = "%04d-%02d-%02d" % (year, month, day)
        fname = "tigge_%s.grb" % (ymd) # grib filename

        fpath = os.path.join(self.gribdatadir,fname) # grib file location

        if not os.path.isfile(fpath):
            print("Downloading %s" % fname,"...")
            # MARS request
            self._tigge_pf_pl_request(ymd,fpath)
        else:
            print("Download already completed.")

        nc_datadir = os.path.join(os.getcwd(), self.netcdfdatadir)
        # Check if netcdf data directory exists, such that .nc files can be saved
        if not os.path.exists(nc_datadir):
            os.makedirs(nc_datadir)

        self._grib2netcdf(fpath,fname.split(".")[0]) # Convert grib file to netcdf

if __name__ == "__main__":
    fetchWind().fetch_grib_from_ecmwf(2014,9,9)

# TIGGE retrieval efficiency (https://confluence.ecmwf.int/display/WEBAPI/TIGGE+retrieval+efficiency)
# The best way to iterate over dates
# for date in dates
#     for time in times
#         TIGGE-request(date, time, origin)
#         (Here you must add everything you need)
