"""
Implementation of the weather module in BlueSky with support for netCDF files.
Author: Remon van den Brandt
Date: 11-12-2018
"""

from netCDF4 import date2num
from scipy import ndimage, interpolate
import numpy as np
import iris
from bluesky.tools.aero import vatmos, kts
import bluesky as bs

class WindIris:
    """
    WindIris class:
        Methods:
            getdata(userlat, userlon, useralt)

            load_file(ensemble, filename)

        Members:
                winddim   = Windfield dimension is automatically set to:
                      3 = 3D field (alt dependent wind at some points)

    Create interpolation and statistical routines that apply to the wind forecast.

    Notes
    -----
    Schematic of the wind data coordinate system:

      +-------------- 90 lat ------------+
      |                |                 |
      |                |                 |
      |                |                 |
      +- 0 ------------+--------- 359.5 -| lon
      |                |                 |
      |                |                 |
      |                |                 |
      +-------------- -90 ---------------+
    """

    def __init__(self):

        self.winddim = 3
        self.filename = None

        self.cubes       = []
        self.grid_lat    = [] # [deg]
        self.grid_lon    = [] # [deg]
        self.pressure = []
        self.forecasts_time = []
        self.realisations = []

        self.north_mean = []
        self.east_mean = []
        self.north = []
        self.east = []

        self.current_ensemble = None
        self.ensemble_loaded = False


    def load_file(self, filename):
        """
         Load netCDF file into memory.
        :param filename: The location of the netCDF file to be loaded.
        :return:
        """

        # load cubes, first the northward wind, then the eastward wind
        # load cubes, first the northward wind, then the eastward wind
        if self.filename != filename or self.filename is None:

            self.filename = filename

            self.cubes = iris.load(self.filename.lower(), ['northward_wind', 'eastward_wind'])

            # convert pressure level from milibars to pascal 200 mbar = 20000 Pa
            self.cubes[0].coord('pressure_level').convert_units('pascal')
            self.cubes[1].coord('pressure_level').convert_units('pascal')

            # get lat,lon,pressure
            self.grid_lat = self.cubes[0].coord('latitude').points   # [deg]
            self.grid_lon = self.cubes[0].coord('longitude').points  # [deg]

            self.grid_lat_spacing = abs(self.grid_lat[1] - self.grid_lat[0])
            self.grid_lon_spacing = abs(self.grid_lon[1] - self.grid_lon[0])

            self.pressure           = self.cubes[0].coord('pressure_level').points # [PA]

            # These are the times used in the simulation
            self.forecasts_time     = self.cubes[0].coord('time').points #

            if self.cubes[0].coords('ensemble_member'):

                # Save the ensemble members
                self.realisations = self.cubes[0].coord('ensemble_member').points

                # mean value of wind over all ensemble members (assumed to be included in the GS)
                # ignore the warning that it generates because it just means there is a gap in the data
                # This can happen with a bounded coordinate if the bounds don't "touch".
                # For example if the bound values were (0 to 10), (10 to 20), and (25 to 35),
                # then there is a gap between 20 and 25. But the post-collapse coordinate would
                # just have bounds of (0, 35) which wouldn't capture the gap.

                self.north_mean = self.cubes[0].collapsed('ensemble_member', iris.analysis.MEAN).data # [m/s]
                self.east_mean = self.cubes[1].collapsed('ensemble_member', iris.analysis.MEAN).data  # [m/s]

            else:

                self.realisations = np.array([])
                self.north = self.cubes[0].data # [m/s]
                self.east = self.cubes[1].data  # [m/s]

            self.current_ensemble = None

            txt = "WIND LOADED FROM {}".format(self.filename)

            return True, txt

    def load_ensemble(self,ensemble):

        # check if cubes contains ensemble members
        if ensemble in self.realisations:


            # if ens member is different from the one currently loaded

            if self.current_ensemble is not ensemble:

                self.north = self.cubes[0].extract(iris.Constraint(ensemble_member=ensemble)).data - \
                             self.north_mean
                self.east = self.cubes[1].extract(iris.Constraint(ensemble_member=ensemble)).data - \
                            self.east_mean

            self.current_ensemble = ensemble
            self.ensemble_loaded  = True

            txt = "ENSEMBLE MEMBER {}".format(self.current_ensemble)

            return True, txt

        else:
            self.ensemble_loaded = False
            txt = "ENSEMBLE MEMBER {}".format(self.current_ensemble)

            return True, txt


    def getdata(self, userlat, userlon, useralt):
        """
        Retrieve the north and south component of the windfield, interpolated at a given positions.
        :param userlat: latitude [deg]
        :param userlon: longitude [deg]
        :param useralt: altitude [m]
        :return: two np.array containting the north component and east component of the wind.
        """

        if self.filename:
            # TODO: find a faster alternative to date2num

            if self.ensemble_loaded:

                pressure = vatmos(useralt)[0]
                time = date2num(bs.sim.utc, units='hours since 1900-01-01 00:00:0.0', calendar='gregorian')
                return self.__interpolate(userlat, userlon, pressure, time)

            else:
                return 0,0

        else:
            return 0, 0


    def __interpolate(self, lat, lon, pressure, time):

        # BlueSky longitude definition: an angular measurement ranging from 0° at the Prime Meridian to +180°
        #  eastward and −180° westward / ECMFW longitude definition: an angular measurement ranging from 0° at
        # the Prime Meridian to +359.5° eastward

        lon = (lon + 360) % 360 # Make longitude periodic for interpolation

        # Find coordinates array index which are used to find, for each point in the output time,pressure,lat,lon
        #  the corresponding coordinates in the input. The value of the input at those coordinates is determined by
        # spline interpolation of the first order

        lon_i = lon / self.grid_lon_spacing         # longitude index in wind array
        lat_i = (90. - lat) / self.grid_lat_spacing  # latitude index in wind array


        # If pressure is outside of forecast range pick the minimum or maximum

        pressure = np.clip(pressure, self.pressure[0], self.pressure[-1])
        pressure_to_index = interpolate.interp1d(self.pressure, range(len(self.pressure)),
                                 bounds_error=True, assume_sorted=True)
        pressure_i = pressure_to_index(pressure)         # pressure index


        time_to_index = interpolate.interp1d(self.forecasts_time, range(len(self.forecasts_time)),
                                 bounds_error=True, assume_sorted=True)
        time_i = time_to_index(time)         # time index


        coord = np.vstack((time_i, pressure_i, lat_i, lon_i))

        # Interpolation
        north = ndimage.map_coordinates(self.north, coord, order=1, mode='wrap')
        east = ndimage.map_coordinates(self.east, coord, order=1, mode='wrap')

        return north, east

    # -----  mimic WindSim class API -------------------
    def get(self, lat, lon, alt=0):
        """
        Get wind vector at given position (and optionally altitude)
        :param lat:
        :param lon:
        :param alt:
        :return:
        """

        vn, ve = self.getdata(lat, lon, alt)

        wdir = (np.degrees(np.arctan2(ve, vn)) + 180) % 360
        wspd = np.sqrt(vn * vn + ve * ve)

        txt = "WIND AT %.5f, %.5f: %03d/%d" % (lat, lon, np.round(wdir), np.round(wspd / kts))

        return True, txt

    def addpoint(self, lat, lon, winddir, windspd, windalt=None):
        # not used
        pass

    def remove(self, idx):
        # not used
        pass

    def add(self, *arg):
        # not used
        pass

    def clear(self):
        # not used
        pass
