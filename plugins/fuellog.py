""" Fuellog: for each aircraft log traffic information when at a waypoint """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack  #, settings, navdb, traf, sim, scr, tools

import numpy as np
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import traf, sim #, settings, navdb, traf, sim, scr, tools
from bluesky.tools import datalog, areafilter, \
    TrafficArrays, RegisterElementParameters
from bluesky import settings

# frequent updates provide an update interval.

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
    "Distance 2D [m], " + \
    "Initial Mass [kg], " + \
    "Actual Mass [kg], " + \
    "Fuel consumption [kg], " + \
    "Work [J], " + \
    "Fuel consumption using work[kg]""\n"

logger = None
### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():

    global logger
    logger = FuelLogger()

    # Addtional initilisation code

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'FUELLOG',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds. By default, your plugin's update function(s)
        # are called every timestep of the simulation. If your plugin needs less
        # frequent updates provide an update interval.
        'update_interval': logger.dt,

        # The update function is called after traffic is updated. Use this if you
        # want to do things as a result of what happens in traffic. If you need to
        # something before traffic is updated please use preupdate.
        'update':          logger.update,

        # The preupdate function is called before traffic is updated. Use this
        # function to provide settings that need to be used by traffic in the current
        # timestep. Examples are ASAS, which can give autopilot commands to resolve
        # a conflict.
        'preupdate':       preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':         reset
        }

    stackfunctions = {
        # The command name for your function
        'LOG': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'LOG ON/OFF',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[onoff]',

            # The name of your function in this plugin
            logger.set,

            # a longer help text of your function.
            'Start logging information']
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions


### Periodic update functions that are called by the simulation. You can replace
### this by anything, so long as you communicate this in init_plugin


class FuelLogger(TrafficArrays):
    """ Traffic area: delete traffic when it leaves this area (so not when outside)"""

    def __init__(self):
        super(FuelLogger, self).__init__()
        # Parameters of area
        self.active = False
        self.dt     = 0.1     # [s] frequency of area check (simtime)
        self.name   = None

        # The FLST logger

        self.logger = datalog.crelog('FUEL', None, header)

        with RegisterElementParameters(self):
            self.at_destination      = np.array([],dtype = np.bool) # At destination or not
            self.create_time = np.array([])
            self.initial_mass = np.array([])
            self.work = np.array([])
            self.distance2D = np.array([])

    def create(self, n=1):
        super(FuelLogger, self).create(n)
        self.create_time[-n:] = sim.simt
        self.initial_mass[-n:] = traf.perf.mass[-n:]


    def update(self):
        """Find out which aircraft are currently at their destination, and
        determine which aircraft need to be deleted."""

        if not self.active:
            return

        resultantspd = np.sqrt(traf.gs * traf.gs + traf.vs * traf.vs)
        self.distance2D += self.dt * traf.gs

        if settings.performance_model == 'openap':
            self.work += (traf.perf.thrust * self.dt * resultantspd)
        else:
            self.work += (traf.perf.Thr * self.dt * resultantspd)

        self.at_destination = np.isclose(traf.lat,traf.actwp.lat,rtol=0.01) & np.isclose(traf.lon,traf.actwp.lon,rtol=0.01)
        wptisdestitnation = np.where(self.at_destination)[0]

        # Log flight statistics when for aircraft at destination
        if len(wptisdestitnation) > 0:

            self.logger.log(
                np.array(traf.id)[wptisdestitnation],
                self.create_time[wptisdestitnation],
                sim.simt - self.create_time[wptisdestitnation],
                self.distance2D[wptisdestitnation],
                self.initial_mass[wptisdestitnation],
                traf.perf.mass[wptisdestitnation],
                self.initial_mass[wptisdestitnation] - traf.perf.mass[wptisdestitnation],
                self.work[wptisdestitnation],
                self.work[wptisdestitnation]/(42.8*1000000)
            )
            # delete all aicraft in self.delidx
            traf.delete(wptisdestitnation)

    def set(self, *args):
        ''' Set Experiment Area. Aicraft leaving the experiment area are deleted.
        Input can be exisiting shape name, or a box with optional altitude constrainsts.'''

        # if all args are empty, then print out the current area status
        if not args:
            return True, "Fuel logging is currently " + ("ON" if self.active else "OFF")
        elif isinstance(args[0],bool):
            if args[0]:
                self.active = True
                self.logger.start()
                return True, "LOG logging is : " + str(self.active)
            else:
                # switch off fuel logging
                self.logger.reset()
                self.active = False
                return True, "LOG is switched : " + str(self.active)
        else:
            return False,  "Incorrect arguments" + \
                           "\nLOG ON/OFF "

def preupdate():
    pass

def reset():
    pass

