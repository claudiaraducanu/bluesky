""" BlueSky plugin template. The text you put here will be visible
    in BlueSky as the description of your plugin. """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack,scr,traf,sim,settings  #, settings, navdb, traf, sim, scr, windtools
from bluesky.tools import datalog, geo, aero, \
    TrafficArrays, RegisterElementParameters
import numpy as np

logger = None
# Log parameters for the flight statistics log
header = \
    "#######################################################\n" + \
    "WAYPOINT LOG\n" + \
    "Flight Statistics\n" + \
    "#######################################################\n\n" + \
    "Parameters [Units]:\n" + \
    "Flight Time [s], " + \
    "Call sign [-], " + \
    "Ensemble Member [-], " + \
    "Forecast time [-], " + \
    "Latitude [deg], " + \
    "Longitude [deg], " + \
    "Altitude [m], " + \
    "TAS [m/s], " + \
    "CAS [m/s], " + \
    "GS  [m/s], " + \
    "Fuel Mass [kg], " + \
    "Mass [kg], "

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():

    # Addtional initilisation code
    global logger
    logger = logWpt()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'WPTLOG',

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
        'preupdate':       logger.preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':         logger.reset
        }

    stackfunctions = {
        # The command name for your function
        'WPTLOG': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'WPTLOG ON/OFF',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[onoff]',

            # The name of your function in this plugin
            logger.set,

            # a longer help text of your function.
            'Print something to the bluesky console based on the flag passed to MYFUN.']
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions


### Periodic update functions that are called by the simulation. You can replace
### this by anything, so long as you communicate this in init_plugin
class logWpt(TrafficArrays):

    def __init__(self):

        super(logWpt, self).__init__()
        # Parameters of area
        self.active = False
        self.dt     = settings.fms_dt   # [s] frequency of area check (simtime)

        # The WPTLOG logger
        self.logger = datalog.crelog('WPTLOG', None, header)

        with RegisterElementParameters(self):
            self.initial_mass                    = np.array([])

    def create(self, n=1):
        super(logWpt, self).create(n)
        self.initial_mass[-n:] = traf.perf.mass


    def log_data(self,idx):

        self.logger.log(

            np.array(traf.id)[idx],
            np.array(traf.type)[idx],
            traf.lat[idx],
            traf.lon[idx],
            traf.alt[idx],
            traf.tas[idx],
            traf.cas[idx],
            traf.gs[idx],
            self.initial_mass[idx] - traf.perf.mass[idx],
            traf.perf.mass[idx])

    def update(self):

        if not self.active:
            pass
        else:
            qdr, distinnm = geo.qdrdist(traf.lat, traf.lon,
                                        traf.actwp.lat, traf.actwp.lon)  # [deg][nm])
            dist = distinnm * aero.nm  # Conversion to meters

            # aircraft for which way-point will get shifted way-points for aircraft i where necessary
            if len(traf.actwp.Reached(qdr, dist, traf.actwp.flyby)):

                # log flight statistics when for aircraft that switches waypoint
                self.log_data(traf.actwp.Reached(qdr, dist, traf.actwp.flyby))

                for idx in traf.actwp.Reached(qdr, dist, traf.actwp.flyby):
                    if traf.ap.route[idx].iactwp == traf.ap.route[idx].nwp - 1:
                        # delete all aicraft in self.delidx
                        traf.delete(idx)

    def preupdate(self):
        pass

    def reset(self):
        pass

    ### Other functions of your plugin
    def set(self,*args):
        # if all args are empty, then print out the current area status
        if not args:
            return True, "Logging at way-point with " \
                         "WPTLOG is currently " + \
                        ("ON" if self.active else "OFF")

        elif isinstance(args[0], bool):

            if args[0]:

                self.logger.start()
                # Log the initial state of all the aircraft in the simulation
                traffic_id = [idx for idx, st in enumerate(traf.id)]
                self.log_data(traffic_id)

                self.active = True
                return True, "WPTLOG logging is : {}".format(self.active)

            else:
                # switch off fuel logging
                self.logger.reset()
                self.active = False
                return True, "WPTLOG is switched : {}".format(self.active)

        return False, "Incorrect arguments" + \
                   "\nWPTLOG ON/OFF "



