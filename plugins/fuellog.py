""" BlueSky fuel consumed plugin. This plugin can use to store information on the fuel used by the aircraft. 
    Statistics on the flight are logged in a data frame
    when the aircraft reaches a way point along its trajectory. At the end of the trajectory the data frame is stored
    in a pickle file.
    This is a condition based logger unlike the standard BlueSky logging tool which is periodic.
"""# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack  #, settings, navdb, traf, sim, scr, windtools
import numpy as np
import pickle
import os
import pandas as pd
from datetime import datetime
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import traf, sim, stack #, settings, navdb, traf, sim, scr, windtools
from bluesky.tools import datalog, areafilter, \
    TrafficArrays, RegisterElementParameters
from bluesky import settings
# Register settings defaults
settings.set_variable_defaults(log_path='output')

# The variables to be stored about the flight
header = \
    ["Simulation time [s] ",
    "Call sign [-] ",
    "Latitude [deg] ",
    "Longitude [deg] ",
    "Altitude [m] ",
    "Ground Speed [m/s] ",
    "CAS [m/s] ",
    "Actual Mass [kg] ",
    "Initial Mass - Actual Mass [kg]",
    "Active Waypoint"] \

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
        'FLOG': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'FLOG ON/OFF',

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

        self.data_log   = None

        # with RegisterElementParameters(self):
        #     self.at_wpt                 = np.array([],dtype = np.bool) # At next active way-point
        #     self.initial_mass           = np.array([])

    # def create(self, n=1):
        # super(FuelLogger, self).create(n)
        # self.initial_mass[-n:] = traf.perf.mass[-n:]

    def update(self):
        """Find out which aircraft are currently at their destination, and
        determine which aircraft need to be deleted."""

        if not self.active:
            pass

        self.at_wpt = np.isclose(traf.lat,traf.actwp.lat,rtol=0.0001) \
                              & np.isclose(traf.lon,traf.actwp.lon,rtol=0.0001)
        ac_at_wpt        = np.where(self.at_wpt)[0]


        if len(ac_at_wpt) > 0:
            condition = np.isclose(float(traf.ap.dest[0].split(',')[0]), traf.actwp.lat, rtol=0.0001) \
                        & np.isclose(float(traf.ap.dest[0].split(',')[1]), traf.actwp.lon, rtol=0.0001)

            for idx in ac_at_wpt:
                self.data_log = self.data_log.append(pd.DataFrame(
                    [[sim.simt, traf.id[idx],
                     traf.lat[idx],
                     traf.lon[idx],
                     traf.alt[idx],
                     traf.gs[idx],
                     traf.cas[idx],
                     traf.perf.mass[idx],
                     self.initial_mass[idx] - traf.perf.mass[idx],traf.ap.route[0].wpname[traf.ap.route[0].iactwp]]],columns=header))
                if condition:
                    traf.delete(idx)
            if condition:
                stack.stack("FLOG OFF")
                stack.stack("QUIT")

    def set(self, *args):

        # if all args are empty, then print out the current area status
        if not args:
            return True, "Logging at way-point with FLOG is currently " + ("ON" if self.active else "OFF")
        elif isinstance(args[0],bool):

            if args[0]:
                self.active = True
                self.data_log = pd.DataFrame(columns=header) # dataframe in which logging information is saved
                return True, "FLOG logging is : ON"
            else:
                # switch off fuel logging
                self.active = False

                # timestamp = datetime.now().strftime('%Y%m%d_%H-%M-%S')
                # fname = os.path.join(os.getcwd(),settings.log_path,"%s_%s_%s.pkl" %("CONDITIONAL", stack.get_scenname(), timestamp))

                return True, "FLOG is switched : OFF"
        else:
            return False,  "Incorrect arguments" + \
                           "\nFLOG ON/OFF "

def preupdate():
    pass

def reset():
    pass

