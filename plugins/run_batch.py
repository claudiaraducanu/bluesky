from bluesky import settings,stack, traf, sim
import os
import datetime
import numpy as np

class Batch:
    def __init__(self):

        self.ic = []
        self.nc = []

        self.scenario_path = os.path.join(settings.scenario_path,"trajectories",
                               datetime.datetime.now().strftime("%d-%m-%Y"))
        self.wind_path     = os.path.join(settings.data_path,"netcdf")

        self.ensembles = []

        self.current_ic = 0
        self.current_ensemble = 1

    def update(self):
        # it the batch is running, check if the ac has landed
        # if self.running:
        #     if not sim.ffmode:
        #         stack.stack('run')
        #         stack.stack('FF')
        #
        #     if not self.takeoff and traf.alt[0] > 10:
        #         self.takeoff = True
        #
        #     if self.takeoff and not traf.swlnav[0]:
        #         stack.stack('hold')
        #         self.results_list.append([self.ic[self.current_scn-1], sim.utc.time(), traf.perf.mass])
        #         self._next()
        # else:
        #     self.start('test', 'data/weather/1day.nc')
        pass

    def preupdate(self):
        pass

    def reset(self):

        self.ic = []
        self.nc = []
        self.ensembles = []
        self.current_ic = None
        self.current_ensemble = None

    def set_batchsim(self,*args):

        # if no arguments provided return the current status of the plugin
        if not args:
            return True, "SIMBATCH is running scenario file: {}".format(self.current_ic) + \
                         "\nCurrently with wind ensemble member: {}".format(self.current_ensemble)

        # Make sure only one argument provided
        if len(args) == 1:

            self.reset()
            # Check if the string length is 1, in which case load all the scenario files from the
            # associated scenario folder.

            if len(args[0]) == 1:

                # For each file check: 1. if it has .scn extension
                scn_files  = np.array(os.listdir(self.scenario_path))
                scn_files  = scn_files[np.core.defchararray.endswith(scn_files, ".scn")]

            # If the string length is larger than 1, this corresponds to an acid and therefore load
            # only the file corresponding to it.
            else:
                # Add scn file extension
                scn_files = np.array([".".join([args[0], "scn"])])

            # scenario file names without extension
            name_files = np.core.defchararray.rstrip(scn_files,'.scn')

            # Vectorized version of the function batch.findFile
            self.vfindFile = np.vectorize(self.findFile)

            # Scenario files.
            scn_paths = np.ones(scn_files.shape, dtype="U32")
            scn_paths[:] =  self.scenario_path
            self.ic = self.vfindFile(scn_files, scn_paths)

            # Index of scn files that are available for simulation

            if self.ic[0] is None :

                return False, "No file with acid: {}".format(name_files) + \
                       "\nexists  to simulate"

            else:

                # Remove the "scenario/" from path.
                self.ic = np.core.defchararray.lstrip(self.ic, "scenario/")

                # Wind files.
                # scenario file names without extension
                name_files = np.core.defchararray.rstrip(scn_files,'.scn')

                wind_extension = np.ones(name_files.shape, dtype="U3")
                wind_extension[:] = 'nc'

                wind_paths = np.ones(name_files.shape, dtype="U11")
                wind_paths[:] = self.wind_path

                self.nc = self.vfindFile(name_files, wind_paths, wind_extension)
                # Index of wind files that are available for simulation
                idx_wfiles = np.where(self.nc != "None")

                # Remove scenario files where there is no wind available for simulation
                self.ic = self.ic[idx_wfiles]
                name_files = name_files[idx_wfiles]

                return True, "SIMBATCH files : {}".format(name_files) + \
                             "\navailable to simulate"

        else:
            return False,"Incorrect number of arguments" + '\nBATCHSIM acid or\n BATCHSIM . '

        # self.nc = nc
        # stack.stack('load_wind {} {}'.format(self.current_ens, self.nc))
        # self.running = True
        # self._next()
        # stack.stack('IC batch/{}'.format(self.ic[0]))
        pass

    @staticmethod
    def findFile(seekName, path, extension=None):

        if extension:
            seekName = ".".join([seekName, extension])

        if os.path.isfile(os.path.join(path, seekName)):
            return os.path.join(path, seekName)
        else:
            return None


    def _next(self):
        # self.ensembles = traf.wind.ens
        # if self.current_scn > len(self.ic)-1:  # if end of scns?)
        #     if self.current_ens < len(self.ensembles):
        #         self.current_ens = self.current_ens + 1
        #         print(self.current_ens)
        #         stack.stack('load_wind {} {}'.format(self.current_ens, self.nc))
        #         self.current_scn = 0
        #         self._next()
        #     else:  # done, store data and go home
        #         df = pd.DataFrame(columns=['id', 'time', 'fuel'], data=self.results_list)
        #         pickle.dump(df, open('output/results.p', 'wb'))
        # else:  # switch to the next scn file
        #     stack.stack('IC batch/{}'.format(self.ic[self.current_scn]))
        #     self.current_scn = self.current_scn + 1
        #     self.takeoff = False
        pass



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
        'update_interval': 1.0,

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
            'BATCHSIM acid or BATCHSIM . ',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[txt]',

            # The name of your function in this plugin
            batch.set_batchsim,

            # a longer help text of your function.
            'Print something to the bluesky console based on the flag passed to MYFUN.'],
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions


