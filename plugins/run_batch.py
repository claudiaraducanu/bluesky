from bluesky import settings,stack, traf, sim
from bluesky.tools import datalog,TrafficArrays,RegisterElementParameters
import os
import datetime
import glob
import numpy as np
from adapt.move_output import move_output

# Initialization function of your plugin. Do not change the name of this
# function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():
    # Additional initialisation code

    batch = Batch()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'BATCHSIM',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds. By default, your plugin's update function(s)
        # are called every timestep of the simulation. If your plugin needs less
        # frequent updates provide an update interval.
        'update_interval': batch.dt,

        # The update function is called after traffic is updated. Use this if you
        # want to do things as a result of what happens in traffic. If you need to
        # something before traffic is updated please use preupdate.
        'update':          batch.update,

        # The preupdate function is called before traffic is updated. Use this
        # function to provide settings that need to be used by traffic in the current
        # timestep. Examples are ASAS, which can give autopilot commands to resolve
        # a conflict.
        'preupdate':       batch.preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':         batch.reset
        }

    stackfunctions = {
        # The command name for your function
        'BATCHSIM': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'BATCHSIM scenario,logType',

            # A list of the argument types your function accepts. For a description of this, see ...
            'txt,txt',

            # The name of your function in this plugin
            batch.set_batchsim,

            # a longer help text of your function.
            'Print something to the bluesky console based on the flag passed to MYFUN.'],
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions

class Batch(TrafficArrays):

    def __init__(self):

        super(Batch, self).__init__()

        self.active = False

        self.ic = []
        self.nc = []

        self.current_scn     = 0
        self.current_nc      = 0
        self.current_member  = 1

        # Parameters of the datalogger
        self.active = False
        self.dt     = 1.0    # [s] frequency of area check (simtime)
        self.logType = None

        with RegisterElementParameters(self):
            self.last_wpt_in_route = np.array([])
            self.actwp_in_route_update = np.array([])

    def update(self):

        #When all aircraft get deleted.
        if not self.active:
            pass

        else:

            if self.logType == "WINDLOG":
                # Determine the last wpt number
                self.actwp_in_route_update[-1:] = [traf.ap.route[idx].iactwp for idx, st in enumerate(traf.id)]
                self.last_wpt_in_route[-1:] = [len(traf.ap.route[idx].wplat) - 1 for idx, st in enumerate(traf.id)]

                acwpt_dest = np.equal(self.last_wpt_in_route, self.actwp_in_route_update)
                acwpt_dest_idx = np.where(acwpt_dest)[0]

                # Log flight statistics when for aircraft that switches waypoint
                if len(acwpt_dest_idx) > 0:

                    at_dest = np.isclose(traf.lat, traf.actwp.lat, rtol=0.0001) & \
                              np.isclose(traf.lon, traf.actwp.lon, rtol=0.0001)
                    at_dest_idx = np.where(at_dest)[0]

                    if len(at_dest_idx) > 0:
                        # delete all aicraft in self.delidx
                        traf.delete(at_dest_idx)

            if len(traf.id) == 0:
                stack.stack("HOLD")

                self.current_member += 1

                if self.current_member <= traf.wind.realisations.size:

                    stack.stack('ensemble_member {}'.format(self.current_member))
                    stack.stack('IC {}'.format(self.ic[self.current_scn]))

                else:
                    # Restart the member count
                    self.current_member = 1
                    # Increase the current wind file counter
                    self.current_nc += 1

                    # Check if there are other wind files to consider
                    if self.current_nc < len(self.nc[self.current_scn]):
                        stack.stack('load_wind {}'.format(self.nc[self.current_scn][self.current_nc]))
                        stack.stack('ensemble_member {}'.format(self.current_member))
                        stack.stack('IC {}'.format(self.ic[self.current_scn]))

                    else:
                        # Restart the file counter
                        self.current_nc = 0
                        self.current_scn += 1

                        if self.current_scn < len(self.ic):
                            stack.stack('load_wind {}'.format(self.nc[self.current_scn][self.current_nc]))
                            stack.stack('ensemble_member {}'.format(self.current_member))
                            stack.stack('IC {}'.format(self.ic[self.current_scn]))
                        else:
                            move_output()
                            stack.stack('QUIT')

    def preupdate(self):

        pass

    def reset(self):
        pass

    def set_batchsim(self,*args):

        # if no arguments provided return the current status of the plugin
        if not args:
            return True, "SIMBATCH is running scenario file: {}".format(self.current_scn) + \
                         "\nCurrently with wind ensemble member: {}".format(self.current_member)

        # Two arguments are required,
        if len(args)  == 2:

            scenarioFilePath = args[0].lower()
            scnExtension = os.path.splitext(scenarioFilePath)[1]

            self.logType = args[1]
            # the string provided is a directory and therefore all files
            # in the directory are analysed.

            if len(scnExtension) == 0:

                twTypeFolder = os.path.join(datetime.datetime.now().strftime("%d-%m-%Y"),
                                            scenarioFilePath)

                for root, dir, files in os.walk(twTypeFolder):
                    self.ic = [os.path.join(twTypeFolder,f) for f in files if f.endswith('.scn')]


            else:
                self.ic.append(os.path.join(datetime.datetime.now().strftime("%d-%m-%Y"),
                                            scenarioFilePath))

            for scn in self.ic:

                date,time = os.path.splitext(scn)[0].split("/")[-1].split("_")[-2],\
                            os.path.splitext(scn)[0].split("/")[-1].split("_")[-1]
                self.nc.append(glob.glob(os.path.join(settings.data_path,'netcdf') +
                                   '/ecmwf_pl_{}_{}_*.nc'.format(date,time), recursive=True))

            # Load the appropriate wind file into memory
            stack.stack('load_wind {}'.format(self.nc[self.current_scn][self.current_nc]))
            stack.stack('ensemble_member {}'.format(self.current_member))
            stack.stack('IC {}'.format(self.ic[self.current_scn]))

            if len(self.ic) != 0:
                self.active = True



                return True, "BATCHSIM files available to simulate"

            else:

                return False, "BATCHSIM does not have any files loaded into memory"
        else:

            return False,"Incorrect number of arguments" + '\nBATCHSIM scenario,logType'



