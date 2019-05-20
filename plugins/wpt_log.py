""" BlueSky plugin template. The text you put here will be visible
    in BlueSky as the description of your plugin. """
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import stack,scr,traf,sim  #, settings, navdb, traf, sim, scr, windtools
from bluesky.tools import datalog, areafilter, geo, \
    TrafficArrays, RegisterElementParameters
import numpy as np

logger = None
header = [' ']
selvars = ['id', 'lat', 'lon', 'alt', 'gs','cas', 'mass']
logprecision = '%.8f'

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
        self.header = header
        self.selvars = selvars

        with RegisterElementParameters(self):
            self.initial_mass                   = np.array([])
            self.last_wpt_lat                 = np.array([traf.ap.route[idx].wplat[-1]
                                                           for idx,st in enumerate(traf.id)])
            self.last_wpt_lon                 = np.array([traf.ap.route[idx].wplon[-1]
                                                           for idx,st in enumerate(traf.id)])

    def create(self, n=1):
        super(logWpt, self).create(n)
        self.initial_mass[-n:] = traf.perf.mass[-n:]

    def update(self):

        if not self.active:
            pass
        else:
            # make sure there are still aircraft
            if traf.id:
                # determine if next waypoint is destination
                next_wpt_dest = np.isclose(traf.actwp.lat, self.last_wpt_lat, rtol=0.001) & \
                                np.isclose(traf.actwp.lon, self.last_wpt_lon, rtol=0.001)
                print(next_wpt_dest)
                # aircraft for which next waypoint is destination
                idx_next_wpt_dest_y = [idx for idx, st in enumerate(next_wpt_dest) if st]

                if len(idx_next_wpt_dest_y) > 0:
                    print(idx_next_wpt_dest_y)
                    # Calculate for each aircraft when it reaches its destination and log data then

                    is_ac_at_dest = np.isclose(traf.lat, self.last_wpt_lat, rtol=0.001) & \
                                    np.isclose(traf.lon, self.last_wpt_lon, rtol=0.001)

                    idx_is_ac_at_dest = [idx for idx, st in enumerate(is_ac_at_dest) if st]

                    # if an aircraft is at the destination
                    if len(idx_is_ac_at_dest) > 0:

                        for idx in idx_is_ac_at_dest:
                            self.log(idx)
                            stack.stack("DEL {}".format(traf.id[idx]))

                idx_next_wpt_dest_n = [idx for idx, st in enumerate(next_wpt_dest) if not st]

                if len(idx_next_wpt_dest_n) > 0:

                    at_wpt = np.isclose(self.preupdate_actwpt_lat,np.array(traf.actwp.lat),rtol= 0.00001) & \
                             np.isclose(self.preupdate_actwpt_lon,np.array(traf.actwp.lon),rtol= 0.00001)

                    idx_at_wpt  = [idx for idx,st in enumerate(at_wpt) if not st]

                    if len(idx_at_wpt) > 0:

                        for idx in idx_at_wpt:
                            self.log(idx)

            else:
                stack.stack("WPTLOG OFF")
                stack.stack("QUIT")

    def preupdate(self):
        if not self.active:
            pass
        else:

            self.preupdate_actwpt_lat = np.array(traf.actwp.lat)
            self.preupdate_actwpt_lon = np.array(traf.actwp.lon)


    def reset(self):

        if self.file:
            self.file.close()
            self.file = None
        self.active = False

    def log(self, idx):

        varlist = [sim.simt, traf.id[idx],
                   traf.lat[idx],
                   traf.lon[idx],
                   traf.alt[idx],
                   traf.gs[idx],
                   traf.cas[idx],
                   traf.perf.mass[idx]]

        # Convert all elements in the  list that are floats to strings with precision 8
        for i, v in enumerate(varlist):
            if isinstance(v, float):
                varlist[i] = logprecision % v

        # log the data to file
        np.savetxt(self.file, np.vstack(varlist).T,
                   delimiter=',', newline='\n', fmt='%s')

    ### Other functions of your plugin
    def set(self,*args):
        # if all args are empty, then print out the current area status
        if not args:
            return True, "Logging at way-point with " \
                         "WPTLOG is currently " + \
                        ("ON" if self.active else "OFF")

        elif isinstance(args[0], bool):
            if args[0]:

                # Create log file name
                filename = datalog.makeLogfileName("WPTLOG")

                # if file exists close it and open again
                if self.file:
                    self.file.close()
                self.file = open(filename, 'wb')
                # Write the header
                for line in self.header:
                    self.file.write(bytearray('# ' + line + '\n', 'ascii'))
                # Write the column contents
                columns = ['simt']
                for var in self.selvars:
                    columns.append(var)
                self.file.write(
                    bytearray('# ' + str.join(', ', columns) + '\n', 'ascii'))

                for idx,id in enumerate(traf.id):
                    self.log(idx)

                if self.file:
                    scr.echo("Data logged in " + filename)
                    self.active = True

                return True, "WPTLOG logging is : {}".format(self.active)

            else:
                # switch off fuel logging
                self.reset()
                return True, "WPTLOG is switched : {}".format(self.active)
        else:
            return False, "Incorrect arguments" + \
                   "\nWPTLOG ON/OFF "



