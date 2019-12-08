from bluesky import settings,stack, traf, sim
from bluesky.tools import TrafficArrays
import datetime
import glob
import numpy as np
import os

# Initialization function of your plugin. Do not change the name of this
# function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():
    # Additional initialisation code

    batch = Batch()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'SBATCH',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds. By default, your plugin's update function(s)
        # are called every timestep of the simulation. If your plugin needs less
        # frequent updates provide an update interval.
        'update_interval':  batch.dt,

        # The update function is called after traffic is updated. Use this if you
        # want to do things as a result of what happens in traffic. If you need to
        # something before traffic is updated please use preupdate.
        'update':           batch.update,

        # The preupdate function is called before traffic is updated. Use this
        # function to provide settings that need to be used by traffic in the current
        # timestep. Examples are ASAS, which can give autopilot commands to resolve
        # a conflict.
        'preupdate':        batch.preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':            batch.reset
        }

    stackfunctions = {
        # The command name for your function
        'SBATCH': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'SBATCH scenario_path',

            # A list of the argument types your function accepts. For a description of this, see ...
            '[txt]',

            # The name of your function in this plugin
            batch.set_sbatch,

            # a longer help text of your function.
            'Simulate the flight plan in the scenario path '],


        'SBATCHSTART': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'SBATCHSTART',

            # A list of the argument types your function accepts. For a description of this, see ...
            '',

            # The name of your function in this plugin
            batch.start,

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
        self.current_scn     = 0

        # Parameters of the datalogger
        self.dt         = 1.0    # [s] frequency of area check (simtime)

    def update(self):

        #When all aircraft get deleted.
        if not self.active:
            pass

        else:
            # Since the way-point log deletes
            if len(traf.id) == 0:
                self.current_scn += 1
                if self.current_scn < len(self.ic):
                    stack.stack('IC {}'.format(self.ic[self.current_scn]))
                else:
                    stack.stack('QUIT')

    def preupdate(self):

        pass

    def reset(self):
        pass

    def set_sbatch(self,*args):

        # if no arguments provided return the current status of the plugin
        if not args:
            return True, "SBATCH is running scenario file: {}".format(self.current_scn)

        elif len(args)  == 1:

            scenarioFilePath   = args[0] # relative to the scenario
            scenarioFilePath   = scenarioFilePath.lower()
            files = [ file for file in os.listdir(os.path.join(settings.scenario_path, scenarioFilePath))
                      if file.endswith(".scn") ]
            self.ic = [os.path.join(scenarioFilePath,file) for file in files]

        else:
            return False,"Incorrect number of arguments"

    def start(self):

        # Load the first wind and scenario file into memory
        stack.stack('IC {}'.format(self.ic[self.current_scn]))

        if len(self.ic) != 0:
            self.active = True
            return True, "SBATCH files available to simulate"
        else:
            return False,"SBATCH does not have any files loaded into memory"


