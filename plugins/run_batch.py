from bluesky import settings,stack, traf, sim
from bluesky.tools import datalog,TrafficArrays,RegisterElementParameters
import os
import datetime
import glob
import numpy as np


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
            'BATCHSIM scenarioFilePath windFilePath',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[txt,txt]',

            # The name of your function in this plugin
            batch.set_batchsim,

            # a longer help text of your function.
            'Print something to the bluesky console based on the flag passed to MYFUN.'],
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions



# def init_scn_files(var):
#
#     scenario_path = os.path.join(settings.scenario_path, "trajectories",
#                                       datetime.datetime.now().strftime("%d-%m-%Y"))
#
#     if len(var) == 1:
#
#         # For each file check: 1. if it has .scn extension
#         scn_files = np.array(os.listdir(scenario_path))
#         scn_files = scn_files[np.core.defchararray.endswith(scn_files, ".scn")]
#
#     # If the string length is larger than 1, this corresponds to an acid and therefore load
#     # only the file corresponding to it.
#     else:
#         # Add scn file extension
#         scn_files = np.array([".".join([var, "scn"])])
#
#     # Vectorized version of the function batch.findFile
#     vfindFile = np.vectorize(findFile)
#
#     # Scenario files.
#     scn_paths = np.ones(scn_files.shape, dtype="U32")
#     scn_paths[:] = scenario_path
#
#     ic = vfindFile(scn_files, scn_paths)
#
#     if ic[0] is None:
#         return None
#
#     else:
#         # Remove the "scenario/" from path.
#         ic = np.core.defchararray.lstrip(ic, "scenario/")
#         return ic,scn_files,vfindFile
#
# def init_wind_files(var):
#     # Wind files.
#     # scenario file names without extension
#     if var is None:
#         return var
#
#     elif len(var) == 3:
#         # scenario file names without extension
#         name_files = np.core.defchararray.rstrip(var[1], '.scn')
#
#         wind_path = os.path.join(settings.data_path, "netcdf")
#
#         wind_extension = np.ones(name_files.shape, dtype="U3")
#         wind_extension[:] = 'nc'
#
#         wind_paths = np.ones(name_files.shape, dtype="U11")
#         wind_paths[:] = wind_path
#
#         nc = var[2](name_files, wind_paths, wind_extension)
#         # Index of wind files that are available for simulation
#         idx_wfiles = np.where(nc != "None")
#
#         # Remove scenario files where there is no wind available for simulation
#         ic = var[0][idx_wfiles]
#         name_files = name_files[idx_wfiles]
#
#         return ic,nc,name_files
#
# def findFile(seekName, path, extension=None):
#
#     if extension:
#         seekName = ".".join([seekName, extension])
#
#     if os.path.isfile(os.path.join(path, seekName)):
#         return os.path.join(path, seekName)
#     else:
#         return None

class Batch(TrafficArrays):

    def __init__(self):

        super(Batch, self).__init__()

        self.active = False

        self.ic = []
        self.nc = []
        # self.running = False
        self.current_scn     = 0
        self.current_member  = 1

        # Parameters of the datalogger
        self.active = False
        self.dt     = 1.0    # [s] frequency of area check (simtime)

    def update(self):
        #When all aircraft get deleted.
        if not self.active:
            pass

        else:
            if not sim.ffmode:
                stack.stack("FF")

            if len(traf.id) == 0:
                stack.stack("HOLD")
                self.current_member += 1

                if self.current_member <= traf.wind.realisations.size:
                    stack.stack('ensemble_member {}'.format(self.current_member))
                    stack.stack('IC {}'.format(self.ic[self.current_scn]))
                else:
                    stack.stack("WPTLOG OFF")
                    self.current_scn += 1
                    if self.current_scn < len(self.ic):
                        stack.stack('load_wind {}'.format(self.nc[self.current_scn]))
                        self.current_member = 1 # Restart the
                        stack.stack('ensemble_member {}'.format(self.current_member))
                        stack.stack('IC {}'.format(self.ic[self.current_scn]))
                    else:
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
            ncFilePath     = args[1].lower()

            # Check if the two strings provided have a file extension,
            # otherwise they are directories
            scnExtension = os.path.splitext(scenarioFilePath)[1]
            ncExtension  = os.path.splitext(ncFilePath)[1]


            # the string provided is a directory and therefore all files
            # in the directory are analysed.

            if len(scnExtension) == 0:
                for root, dir, files in os.walk(scenarioFilePath):
                    for f in files:
                        if f.endswith('.scn'):
                            self.ic.append(os.path.join(settings.scenario_path,
                                                        datetime.datetime.now().strftime("%d-%m-%Y"),
                                                        f))
            else:
                self.ic.append(os.path.join(settings.scenario_path,
                                            datetime.datetime.now().strftime("%d-%m-%Y"),
                                            scenarioFilePath))

            if len(ncExtension) == 0:
                for root, dir, files in os.walk(scenarioFilePath):
                    for f in files:
                        if f.endswith('.scn'):
                            self.nc.append(os.path.join(settings.data_path,"netcdf",f))
            else:
                self.nc.append(os.path.join(settings.data_path,"netcdf",
                                            datetime.datetime.now().strftime("%d-%m-%Y"),
                                            ncFilePath))

                # Load the appropriate wind file into memory
            stack.stack('load_wind {}'.format(self.nc[self.current_scn]))
            stack.stack('ensemble_member {}'.format(self.current_member))
            stack.stack('IC {}'.format(self.ic[self.current_scn]))

            if len(self.ic) != 0:
                self.active = True

                return True, "SIMBATCH files available to simulate"

            else:

                return False, "SIMBATCH does not have any files loaded into memory"
        else:

            return False,"Incorrect number of arguments" + '\nBATCHSIM scenarioFilePath windFilePath '



