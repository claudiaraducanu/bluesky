""" BlueSky fuel consumption plugin. """
import numpy as np
import math
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import traf, sim #, settings, navdb, traf, sim, scr, tools
from bluesky.tools import datalog, areafilter, \
    TrafficArrays, RegisterElementParameters
from bluesky.tools.aero import ft
from bluesky import settings

# Log parameters for the flight statistics log
header = \
    "#######################################################\n" + \
    "FUEL LOG\n" + \
    "Flight Statistics\n" + \
    "#######################################################\n\n" + \
    "Parameters [Units]:\n" + \
    "Deletion Time [s], " + \
    "Call sign [-], " + \
    "Spawn Time [s], " + \
    "Flight time [s], " + \
    "Initial Mass [kg], " + \
    "Actual Mass [kg], " + \
    "Fuel consumption [kg], " + "\n"

# Global data
logger = None

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():

    # Addtional initilisation code
    global logger
    logger = FuelLogger()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'AREA',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds.
        'update_interval': logger.dt,

        # The update function is called after traffic is updated.
        'update':          logger.update,
        }

    stackfunctions = {
        "AREA": [
            "AREA ON/OFF",
            "[float/txt,float,float,float,alt,alt]",
            logger.set,
            "Define experiment area (area of interest)"
        ]
    }
    # init_plugin() should always return these two dicts.
    return config, stackfunctions

class FuelLogger(TrafficArrays):
    """ Traffic area: delete traffic when it leaves this area (so not when outside)"""
    def __init__(self):
        super(FuelLogger, self).__init__()
        # Parameters of area
        self.active = False
        self.dt     = 0.1     # [s] frequency of area check (simtime)
        self.name   = None

        # The FLST logger

        self.logger = datalog.crelog('FUELLOG', None, header)

        with RegisterElementParameters(self):
            self.at_destination      = np.array([],dtype = np.bool) # At destination or not
            self.create_time = np.array([])
            self.initial_mass = np.array([])

    def create(self, n=1):
        super(FuelLogger, self).create(n)
        self.create_time[-n:] = sim.simt
        self.initial_mass[-n:] = traf.perf.mass[-n:]


    def update(self):
        """Find out which aircraft are currently at their destination, and
        determine which aircraft need to be deleted."""

        if not self.active:
            return

        self.at_destination = np.isclose(traf.lat,traf.actwp.lat,rtol=0.01) & np.isclose(traf.lon,traf.actwp.lon,rtol=0.01)
        wptisdestitnation = np.where(self.at_destination)[0]

        # Log flight statistics when for aircraft at destination
        if len(wptisdestitnation) > 0:
            print(wptisdestitnation)

            self.logger.log(
                np.array(traf.id)[wptisdestitnation],
                self.create_time[wptisdestitnation],
                sim.simt - self.create_time[wptisdestitnation],
                self.initial_mass[wptisdestitnation],
                traf.perf.mass[wptisdestitnation],
                self.initial_mass[wptisdestitnation] - traf.perf.mass[wptisdestitnation],
            )
            # delete all aicraft in self.delidx
            traf.delete(wptisdestitnation)

    def set(self, *args):
        ''' Set Experiment Area. Aicraft leaving the experiment area are deleted.
        Input can be exisiting shape name, or a box with optional altitude constrainsts.'''

        # if all args are empty, then print out the current area status
        if not args:
            return True, "Fuel logging is currently " + ("ON" if self.active else "OFF")

        if isinstance(args[0],str):
            if args[0]=="ON":
                self.active = True
                self.logger.start()
                return True, "FUELLOG logging is : " + str(self.active)
            if args[0]=='OFF' or args[0]=='OF':
                # switch off fuel logging
                self.logger.reset()
                self.active = False
                return True, "FUELLOG is switched : " + str(self.active)

        return False,  "Incorrect arguments" + \
                       "\nFUELLOG ON/OFF "


