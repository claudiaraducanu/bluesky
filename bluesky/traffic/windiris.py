"""
Implementation of the weather module in BlueSky with support for netCDF files.
The module assumes only the difference of the wind in comparison to the
average wind of the complete ensemble set.

NOTE:
This WindIris module will only work correctly if the DATE is set before loading
the wind data.

Original Author: Remon van den Brandt
Update Author: René Verbeek
Date: 17-5-2019
"""


from netCDF4 import date2num, num2date
from scipy import ndimage, interpolate
import numpy as np
import iris
from bluesky.tools.aero import vatmos, kts
import bluesky as bs


class WindIris:
    """
    Create interpolation and statistical routines that apply to the wind forecast.

    Notes
    -----
    Schematic of the coordinate system:

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
        self.cubes = []
        self.lat = []
        self.lon = []
        self.pressure = []
        self.t = []
        self.lat_stepsize = None
        self.lon_stepsize = None
        self.lat_first = None
        self.lon_first = None
        self.time1_num = None
        self.time0_num = None
        self.time0_utc_num = None
        self.time0_sim = None
        self.north_mean = []
        self.east_mean = []
        self.ens = []
        self.north = []
        self.east = []
        self.__ens = []

        self.__loaded = False

    def _get_wind(self, lat, lon, pressure, time, ens=None):
        """
        Retrieve the north and south component of the windfield, interpolated at a given positions.

        Parameters
        ----------
        lat: array_like
            latitude.
        lon: array_like
            Longitude.
        pressure: array_like
            Pressure in Pa.
        time: datetime
            timestamp.
        ens: int, optional
            Ensemble member.

        Returns
        -------
        north: array_like
             North component of the wind.
        east: array_like
            East component of the wind.
        """

        if self.__loaded:
            if ens:
                self.__load_ensemble(ens)
            return self.__interpolate(self.north, self. east, lat, lon, pressure, time)
        else:
            return 0, 0

    def load_file(self, ensemble, filename):
        """ Load netCDF file into memory.

        Parameters
        ----------
        ensemble : int
            The number of the ensemble to be loaded.
        filename : str
            The location of the netCDF file to be loaded.
        """

        self.cubes = iris.load(filename.lower(), ['northward_wind', 'eastward_wind'])
        self.cubes[0].coord('pressure_level').convert_units('pascal')
        self.cubes[1].coord('pressure_level').convert_units('pascal')

        self.lat = self.cubes[0].coord('latitude').points
        self.lon = self.cubes[0].coord('longitude').points

        self.lat_stepsize =self.cubes[0].coord('latitude').points[1] - self.cubes[0].coord('latitude').points[0]
        self.lon_stepsize = self.cubes[0].coord('longitude').points[1] - self.cubes[0].coord('longitude').points[0]
        self.lat_first = self.cubes[0].coord('latitude').points[0]
        self.lon_first = self.cubes[0].coord('longitude').points[0]

        self.pressure = self.cubes[0].coord('pressure_level').points
        self.t = self.cubes[0].coord('time').points
        self.time0_utc_num = date2num(bs.sim.utc, units='hours since 1900-01-01 00:00:0.0', calendar='gregorian') * 3600
        self.time0_sim = bs.sim.simt
        self.time1_num = self.cubes[0].coord('time').points[1] * 3600.
        self.time0_num = self.cubes[0].coord('time').points[0] * 3600.

        if self.cubes[0].coords('ensemble_member'):
            self.ens = self.cubes[0].coord('ensemble_member').points
            self.north_mean = self.cubes[0].collapsed('ensemble_member', iris.analysis.MEAN).data
            self.east_mean = self.cubes[1].collapsed('ensemble_member', iris.analysis.MEAN).data
        else:
            self.ens = []
            self.north = self.cubes[0].data
            self.east = self.cubes[1].data
        self.__ens = []
        self.__load_ensemble(ensemble)

        self.__loaded = True

    # -----  mimic windsim class API -------------------
    def get(self, lat, lon, alt=0):
        """ Get wind vector at given position (and optionally altitude) """

        vn, ve = self.getdata(lat, lon, alt)

        wdir = (np.degrees(np.arctan2(ve, vn)) + 180) % 360
        wspd = np.sqrt(vn * vn + ve * ve)

        txt = "WIND AT %.5f, %.5f: %03d/%d" % (lat, lon, np.round(wdir), np.round(wspd / kts))

        return True, txt

    def getdata(self, userlat, userlon, useralt=0.0):
        """ Retrieve the north and south component of the windfield, interpolated at a given positions.

        Parameters
        ----------
        userlat : float
            Latitude [deg]
        userlon : float
            Longitude [deg]
        userlat : float
            Altitude [m]

        Returns
        -------
        north: array_like
             North component of the wind.
        east: array_like
            East component of the wind.
         """
        p = vatmos(useralt)[0]
        time = bs.sim.simt

        return self._get_wind(userlat, userlon, p, time)

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

    @property
    def ensembles(self):
        if self.ens.any():
            return self.cubes[0].coord('ensemble_member').points
        else:
            return [1]

    @property
    def time(self):
        """Time instance of forecast in hours since 1900-01-01 00:00:0.0"""
        return num2date(self.cubes[0].coord('time').points, units='hours since 1900-01-01 00:00:0.0',
                        calendar='gregorian')

    def __load_ensemble(self, ens):
        # check if cubes contains ensemble members
        if list(self.ens):
            # if ens member is different from the one currently loaded
            if self.__ens is not ens:
                self.north = self.cubes[0].extract(iris.Constraint(ensemble_member=ens)).data - self.north_mean
                self.east = self.cubes[1].extract(iris.Constraint(ensemble_member=ens)).data - self.east_mean
            self.__ens = ens

    def __interpolate(self, cube_n, cube_e, lat, lon, pressure, time):
        lon = (lon + 360) % 360

        # find coordinates, assumes grid starting at lon 0.0 and lat 90.0
        lon_i = lon / self.lon_stepsize
        lat_i = (lat - 90) / self.lat_stepsize

        # saturate pressure altitude
        pressure = np.clip(pressure, self.pressure[0], self.pressure[-1])
        f = interpolate.interp1d(self.pressure, range(len(self.pressure)), bounds_error=True, assume_sorted=True)
        pres_i = f(pressure)

        time_i = (time - self.time0_sim) / (self.time1_num - self.time0_num)

        # TODO check for out of bounds
        coord = np.vstack(np.broadcast_arrays(time_i, pres_i, lat_i, lon_i))

        # TODO The wrap around also wraps around the time, which does not give the correct behaviour.
        north = ndimage.map_coordinates(cube_n, coord, order=1, mode='wrap')
        east = ndimage.map_coordinates(cube_e, coord, order=1, mode='wrap')
        return north, east