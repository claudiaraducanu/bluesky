""" Fuellog: for each aircraft log traffic information when at a waypoint """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack  #, settings, navdb, traf, sim, scr, tools

import numpy as np
import csv
from datetime import datetime
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import traf, sim, stack #, settings, navdb, traf, sim, scr, tools
from bluesky.tools import datalog, areafilter, \
    TrafficArrays, RegisterElementParameters
from bluesky import settings
# Register settings defaults
settings.set_variable_defaults(log_path='output')

# frequent updates provide an update interval.

csv_header = \
    ["Simulation time [s] ",
    "Call sign [-] ",
    "Latitude [deg] ",
    "Longitude [deg] ",
    "Altitude [m] ",
    "Actual Mass [kg] ",
    "Active Way-poiny lat ",
    "Active Way-point lon"] \

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


        self.file   = None
        self.csv_writer = None
        self.header = csv_header

        with RegisterElementParameters(self):
            self.at_wpt                 = np.array([],dtype = np.bool) # At next active way-point

    def update(self):
        """Find out which aircraft are currently at their destination, and
        determine which aircraft need to be deleted."""

        if not self.active:
            pass

        self.at_wpt = np.isclose(traf.lat,traf.actwp.lat,rtol=0.00001) \
                              & np.isclose(traf.lon,traf.actwp.lon,rtol=0.00001)
        ac_at_wpt        = np.where(self.at_wpt)[0]

        if len(ac_at_wpt) > 0:
            condition = np.isclose(float(traf.ap.dest[0].split(',')[0]), traf.actwp.lat, rtol=0.0001) \
                        & np.isclose(float(traf.ap.dest[0].split(',')[1]), traf.actwp.lon, rtol=0.0001)

            for idx in ac_at_wpt:
                self.csv_writer(
                    [sim.simt, traf.id[idx],
                     traf.lat[idx],
                     traf.lon[idx],
                     traf.alt[idx],
                     traf.perf.mass[idx],
                     traf.actwp.lat[idx],
                     traf.actwp.lon[idx]]
                )
                if condition:
                    traf.delete(idx)
            if condition:
                self.set((False,))

    def set(self, *args):

        # if all args are empty, then print out the current area status
        if not args:
            return True, "Fuel logging is currently " + ("ON" if self.active else "OFF")
        elif isinstance(args[0],bool):
            if args[0]:
                self.active = True
                self.start()
                return True, "LOG logging is : " + str(args[0])
            else:
                # switch off fuel logging
                self.active = False
                self.reset()
                return True, "LOG is switched : " + str(args[0])
        else:
            return False,  "Incorrect arguments" + \
                           "\nLOG ON/OFF "

    def start(self):

        fname = datalog.makeLogfileName("FUEL_CSV")

        if self.file:
            self.file.close()
        self.file       = open(fname, 'w')
        self.csv_writer = csv.writer(self.file).writerow # Function to write a row in csv
        # Write the header
        self.csv_writer(self.header)

    def reset(self):
        if self.file:
            self.file.close()
            self.file   = None
            self.csv_writer = None


def preupdate():
    pass

def reset():
    pass

