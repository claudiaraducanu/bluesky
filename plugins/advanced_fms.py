""" BlueSky advanced FMS plugin. It allows for functions such as RTA """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack,traf  #, settings, navdb, traf, sim, scr, windtools
from bluesky.tools.trafficarrays import TrafficArrays, RegisterElementParameters
from bluesky.traffic.performance.legacy.performance import PHASE
from plugins.patch_route import patch_route
from datetime import datetime,time
import numpy as np

rtafms = None

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():

    # Addtional initilisation code

    global rtafms
    rtafms = advancedFMS()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'ADFMS',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds. By default, your plugin's update function(s)
        # are called every timestep of the simulation. If your plugin needs less
        # frequent updates provide an update interval.
        'update_interval': 2.5,

        # The update function is called after traffic is updated. Use this if you
        # want to do things as a result of what happens in traffic. If you need to
        # something before traffic is updated please use preupdate.
        'update':           rtafms.update,

        # The preupdate function is called before traffic is updated. Use this
        # function to provide settings that need to be used by traffic in the current
        # timestep. Examples are ASAS, which can give autopilot commands to resolve
        # a conflict.
        'preupdate':        rtafms.preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':            rtafms.reset
        }

    stackfunctions = {
        # The command name for your function
        'WPRTA': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'WPRTA acid,wpname,HH:MM:SS.ss',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[acid,wp/txt,txt]',

            # The name of your function in this plugin
            rtafms.set_rta,

            # a longer help text of your function.
            'Print something to the bluesky console based on the flag passed to MYFUN.'],

        'WPTW': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'WPTW acid,wpname,tw',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[acid,wp/txt,float]',

            # The name of your function in this plugin
            rtafms.set_tw,

            # a longer help text of your function.
            ' '],
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions


### Periodic update functions that are called by the simulation. You can replace
### this by anything, so long as you communicate this in init_plugin

class advancedFMS(TrafficArrays):

    def __init__(self):

        super(advancedFMS, self).__init__()

        self.dt                                 = 60    # [s] frequency of afms update (simtime)
        self.twdefault                          = 60.0    # [s] standard time window size for
        patch_route(self.twdefault)
        self.afms_mode = ['OFF','CONTINUE','RTA','TW']

        with RegisterElementParameters(self):
            # Advanced FMS required time of arrival
            self.next_wprta   = np.array([])  # next way-point in route with RTA

    def update(self):
        pass

    def preupdate(self):

        for idx,_ in enumerate(traf.id):
            if int(traf.perf.phase[idx]) == PHASE['CR']:

            # find remaining way-points in the route and then
            traf.ap.route[idx].wpmode[traf.ap.route[idx].iactwp:]

            rta_index = next((index for index, value in enumerate(traf.ap.route[idx].wpmode[traf.ap.route[idx].iactwp:]) if
                              isinstance(value, time)), -1)

    def reset(self):
        pass

    ### Other functions of your plugin
    def set_rta(self,*args):

        if len(args) != 3:
            return False, 'RTA function requires 3 arguments acid, wpname and HH:MM:SS'
        else:

            idx,name,wprtatime  = args[0],args[1],args[2]

            if name in traf.ap.route[idx].wpname:

                wpidx = traf.ap.route[idx].wpname.index(name)
                traf.ap.route[idx].wprta[wpidx] = datetime.strptime(wprtatime, '%H:%M:%S').time()
                traf.ap.route[idx].wpmode[wpidx] = 2

                return True, "RTA " + traf.id[idx] + " way-point " + name + " at " + \
                       wprtatime + " added."

    ### Other functions of your plugin
    def set_tw(self,*args):

        if len(args) != 3:
            return False, 'RTA function requires 3 arguments acid, wpname, HH:MM:SS and time window'
        else:

            idx,name,tw  = args[0],args[1],args[2]

            if name in traf.ap.route[idx].wpname:

                wpidx = traf.ap.route[idx].wpname.index(name)
                
                traf.ap.route[idx].wptw[wpidx]      = tw
                traf.ap.route[idx].wpmode[wpidx]    = 3

                return True, "RTA " + traf.id[idx] + " way-point " + name + \
                       + " with time window " + tw + " added."


