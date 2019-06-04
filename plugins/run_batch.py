from bluesky import settings,stack, traf, sim
import os
import datetime


class Batch:
    def __init__(self):

        self.ic = []
        self.nc = []

        self.scenario_path = os.path.join(settings.scenario_path,"trajectories",
                               datetime.datetime.now().strftime("%d-%m-%Y"))
        self.wind_path     = os.path.join(settings.data_path,"netcdf")


        self.running = False
        self.takeoff = False

        self.ensembles = []
        self.results_list = []

        self.current_ic = None
        self.current_ensemble = None

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
        pass

    def set_batchsim(self,*args):

        # if no arguments provided return the current status of the plugin
        if not args:
            return True, "SIMBATCH is running scenario file: {}".format(self.current_ic) + \
                         "\nCurrently with wind ensemble member: {}".format(self.current_ensemble)

        if len(args) == 1:

            if len(args[0]) == 1:

                # Select all files from the
                for f in os.listdir(self.scenario_path):
                    if f.endswith('.scn'):
                        self.ic.append(f)

                return True, "SIMBATCH is running all files in {}".format(self.scenario_path)

            else:

                f = self.findFile(seekName=args[0],
                                             path=self.scenario_path,
                                             extension='scn')

                if f:
                    self.ic.append(f)
                    return True, "Unknown trajectory file {}".format(args[0]) + \
                                    "\nCheck {} for file".format(self.scenario_path)

                else:

                    return False, "Unknown trajectory file {}".format(args[0]) + \
                                "\nCheck {} for file".format(self.scenario_path)

        

        return False,"Incorrect number of arguments" + '\nBATCHSIM acid or\n BATCHSIM . '

        # folder = '/home/remonvandenbra/repo/bluesky/scenario/batch'
        # for f in os.listdir(folder):
        #     if f.endswith('.scn'):
        #         self.ic.append(f)
        #
        # self.nc = nc
        # stack.stack('load_wind {} {}'.format(self.current_ens, self.nc))
        # self.running = True
        # self._next()
        # stack.stack('IC batch/{}'.format(self.ic[0]))
        pass

    @staticmethod
    def findFile(seekName,path,extension):

        filename = ".".join([seekName,extension])

        if os.path.isfile(filename):
            return filename

        elif os.path.isfile(os.path.join(path,filename)):
            return os.path.join(path,filename)

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


