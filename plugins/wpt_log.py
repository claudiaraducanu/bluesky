""" BlueSky plugin template. The text you put here will be visible
    in BlueSky as the description of your plugin. """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack,scr,traf,sim  #, settings, navdb, traf, sim, scr, windtools
from bluesky.tools import datalog, areafilter, geo, \
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
    "Latitude [deg], " + \
    "Longitude [deg], " + \
    "Altitude [m], " + \
    "TAS [m/s], " + \
    "CAS [m/s] " + \
    "GS  [m/s] " + \
    "Mass [kg] "

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
        self.dt     = 1.0    # [s] frequency of area check (simtime)
        self.file   = None

        # The WPTLOG logger
        self.logger = datalog.crelog('WPTLOG', None, header)

        with RegisterElementParameters(self):
            self.last_wpt_in_route        = np.array([])
            self.actwp_in_route_preupdate        = np.array([])
            self.actwp_in_route_update           = np.array([])

    def log_data(self,idx):

        self.logger.log(
            np.array(traf.id)[idx],
            traf.wind.current_ensemble,
            traf.lat[idx],
            traf.lon[idx],
            traf.alt[idx],
            traf.tas[idx],
            traf.cas[idx],
            traf.gs[idx],
            traf.perf.mass[idx],
        )

    def update(self):

        if not self.active:
            pass
        else:

            self.actwp_in_route_update[-1:] = [traf.ap.route[idx].iactwp for idx, st in enumerate(traf.id)]
            switch_wpt     = np.equal(self.actwp_in_route_preupdate,self.actwp_in_route_update)
            switch_wpt_idx = np.where(switch_wpt == False)[0]

            # Log flight statistics when for aircraft that switches waypoint
            if len(switch_wpt_idx) > 0:

                self.log_data(switch_wpt_idx)
                # delete all aicraft in self.delidx

            # Determine the last wpt number
            self.last_wpt_in_route[-1:] = [len(traf.ap.route[idx].wplat)-1 for idx, st in enumerate(traf.id)]

            acwpt_dest         = np.equal(self.last_wpt_in_route,self.actwp_in_route_update)
            acwpt_dest_idx     = np.where(acwpt_dest)[0]


            #Log flight statistics when for aircraft that switches waypoint
            if len(acwpt_dest_idx) > 0:

                at_dest = np.isclose(traf.lat, traf.actwp.lat, rtol=0.0001) & \
                                np.isclose(traf.lon, traf.actwp.lon, rtol=0.0001)
                at_dest_idx = np.where(at_dest)[0]

                if len(at_dest_idx) > 0:

                    self.log_data(at_dest_idx)

                    # delete all aicraft in self.delidx
                    traf.delete(at_dest_idx)

    def preupdate(self):

        if not self.active:
            pass
        else:
            self.actwp_in_route_preupdate[-1:] = [traf.ap.route[idx].iactwp for idx, st in enumerate(traf.id)]

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



