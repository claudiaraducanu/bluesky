""" Flight Management System Mode plugin """
# Import the global bluesky objects. Uncomment the ones you need
import  datetime
from plugins.patch_route import patch_route
# from math import sqrt
import numpy as np

from bluesky import sim, stack, traf, settings
from bluesky.tools import datalog,aero,geo,TrafficArrays, RegisterElementParameters
from bluesky.traffic.performance.legacy.performance import PHASE
# Global data
afms = None
header = \
    "#######################################################\n" + \
    "FMS LOG\n" + \
    "Flight Statistics\n" + \
    "#######################################################\n\n" + \
    "Parameters [Units]:\n" + \
    "simulation time [s], flight time, " + \
    "active waypoint, " + \
    "active rta waypoint, " + \
    "eta [s] \n" + \
    "simulation time [s], flight time, rta time, " + \
    "active waypoint, " + \
    "active rta waypoint, " + \
    "eta [s], rta [s], latest rta [s], left_out, right_out," + \
    "gs [m/s], tas[m/s], cas[m/s], new cas [m/s] "

def init_plugin():

    afms = Afms()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'AFMS',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds. By default, your plugin's update function(s)
        # are called every timestep of the simulation. If your plugin needs less
        # frequent updates provide an update interval.
        'update_interval':  afms.dt,

        # The update function is called after traffic is updated. Use this if you
        # want to do things as a result of what happens in traffic. If you need to
        # something before traffic is updated please use preupdate.
        'update':           afms.update,

        # The preupdate function is called before traffic is updated. Use this
        # function to provide settings that need to be used by traffic in the current
        # timestep. Examples are ASAS, which can give autopilot commands to resolve
        # a conflict.
        'preupdate':        afms.preupdate,

        # If your plugin has a state, you will probably need a reset function to
        # clear the state in between simulations.
        'reset':            afms.reset
        }

    stackfunctions = {
        # The command name for your function
        'AFMS': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'AFMS acid ON/OFF',

            # A list of the argument types your function accepts. For a description of this, see ...
            'acid,onoff',

            # The name of your function in this plugin
            afms.set_mode,

            # a longer help text of your function.
            'AFMS_FROM command that sets the mode of the Advanced FMS from a specified waypoint.'
            'The choice is between: CONTINUE (continue with current advanced FMS mode), OFF (turn advanced FMS off ),'
            'RTA (aim to arrive just in time at the next RTA time constraint), and TW (aim to arrive within the'
            'time window at the next Time Window constraint). In case of OWN/TW mode you must specify additionally'
            'the own speed (=preferred speed) using the OWN_SPEED_FROM command'],
        'RTA': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'RTA acid,wpname,day,month,year,HH:MM:SS',

            # A list of the argument types your function accepts. For a description of this, see ...
            'acid,wpinroute,int,int,int,txt',

            # The name of your function in this plugin
            afms.set_rta,

            # a longer help text of your function.
            'RTA command that sets the time at which the aircraft should arrive at the'
            'specified way-point.'],
        ''
        'TW': [
            # A short usage string. This will be printed if you type HELP <name> in the BlueSky console
            'TW acid,time_window_size',

            # A list of the argument types your function accepts. For a description of this, see ...
            'acid,int',

            # The name of your function in this plugin
            afms.set_tw,

            # a longer help text of your function.
            'TW command  sets the time window size in seconds for each way-point along the aircraft route'
            'with a RTA constraint.'],
    }

    # init_plugin() should always return these two dicts.
    return config, stackfunctions


### Periodic update functions that are called by the simulation. You can replace
### this by anything, so long as you communicate this in init_plugin

class Afms(TrafficArrays):
    """ Advanced FMS: dynamically adjust speed of flights based on set AFMS mode and/or RTA/Time Window"""

    def __init__(self):
        super(Afms, self).__init__()
        # Parameters of afms
        self.dt                                     = settings.fms_dt # [s] frequency of AFMS update
        self.time_tolerance                         = 6.0             # [s]

        # Path the route class with some extra default variables to store route information associate to time windows
        patch_route()

        with RegisterElementParameters(self):
            self.afms_on               = np.array([],dtype = np.bool) # AFMS on or off
            self.tw_length             = np.array([])


    def create(self, n=1):
        super(Afms, self).create(n)
        self.afms_on[-n:]      = False
        self.tw_length[-n:]    = 0.0

    def set_rta(self,*args):

        if len(args) != 6:
            return False, 'RTA function requires 6 arguments acid, wpname,day,month,year,HH:MM:SS'
        else:

            idx,name,day,month,year,wprtatime  = args[0],args[1],args[2],args[3],args[4],args[5]

            # make sure that the way-point exists
            if name in traf.ap.route[idx].wpname:

                wpidx = traf.ap.route[idx].wpname.index(name)
                traf.ap.route[idx].wprta[wpidx] = datetime.datetime.strptime(
                                                    f'{year},{month},{day},{wprtatime}',
                                                    '%Y,%m,%d,%H:%M:%S.%f' if '.' in wprtatime else
                                                    '%Y,%m,%d,%H:%M:%S')
                traf.ap.route[idx].rta.append(wpidx)

                return True, traf.id[idx] + " has rta at way-point " + name + " at " + \
                       wprtatime + " added."
            else:
                return False, "Unknown way-point " + name

    def set_tw(self, *args):

        if len(args) != 2:
            return False, 'TW needs 2 arguments acid, twsize'
        else:
            idx,tw_size = args[0],args[1]
            self.tw_length[idx] = tw_size

            return True, traf.id[idx] + " time window length set for " + str(tw_size) + " seconds"

    def set_mode(self, *args):

        if len(args) != 2:
            return False, 'AFMS needs 2 arguments'
        else:

            idx,onoff = args[0], args[1]

            if  onoff:
                # add the aircraft to the list of aircraft with advanced fms mode on
                self.afms_on[idx] = onoff
                # sort the way-points with RTA in the order in which they are encountered in route
                traf.ap.route[idx].rta.sort()
                # set the current active way-point with RTA to the first element in the way-points with RTA list
                traf.ap.route[idx].iacwprta     = traf.ap.route[idx].rta[0]
                # remove the active rta from the list
                traf.ap.route[idx].rta          = traf.ap.route[idx].rta[1:]

                self.logger = datalog.crelog('FMSLOG', None, header=" ")
                self.logger.start()

                return True, "AFMS is currently active for  " + traf.id[idx]

            elif not onoff:
                # add the aircraft to the list of aircraft with advanced fms mode on
                self.afms_on[idx] = onoff
                self.logger.reset()

            else:
                return False, "Unknown argument!"

    def update(self):

        pass

    def reset(self):  #
        pass

    def preupdate(self):

        # check if for any aircraft the AFMS mode is active
        if not self.afms_on.any():
            pass
        else:
            afmsIds = np.where(self.afms_on)[0]

            for idx in afmsIds:

                if int(traf.perf.phase[idx]) != PHASE['CR']:
                    pass
                else:

                    """Define time window at current active way-point with time constraint"""
                    tw_opening, tw_closing = self.define_tw(idx)

                    if (traf.ap.route[idx].iacwprta < traf.ap.route[idx].iactwp or tw_closing < 0) \
                        and len(traf.ap.route[idx].rta):

                        # switch to next way-point with time constraint
                        traf.ap.route[idx].iacwprta = traf.ap.route[idx].rta[0]
                        # remove the active rta from the list
                        traf.ap.route[idx].rta = traf.ap.route[idx].rta[1:]

                        dist2rta       = self.dimensions2rta(idx)
                        # Final ETA calculation
                        eta            = np.sum(np.divide(dist2rta, traf.tas[idx]))
                        time_tolerance = self.dead_band(eta)

                        """Define time window at current active way-point with time constraint"""
                        tw_opening, tw_closing = self.define_tw(idx)
                        self.adherence_tw(idx, eta, tw_opening, tw_closing,time_tolerance)

                    elif (traf.ap.route[idx].iacwprta < traf.ap.route[idx].iactwp or tw_closing < 0) \
                            and not len(traf.ap.route[idx].rta):
                        self.afms_on[idx] = False

                    else:
                        """
                        Compute estimated time of arrival (ETA) at the current active way-point with RTA constraint
                        wth the current calibrated airspeed (CAS)
                        """
                        """Compute the ETA and the corresponding flight time"""
                        dist2rta = self.dimensions2rta(idx)
                        eta = np.sum(np.divide(dist2rta, traf.tas[idx]))
                        time_tolerance = self.dead_band(eta)

                        self.adherence_tw(idx, eta, tw_opening, tw_closing,time_tolerance)


    def adherence_tw(self, idx, eta, tw_opening, tw_closing, tolerance):

        # There must be some tolerance between the ETA and RTA to minimize throttle activity.
        # First scenario is that the aircraft arrives earlier than the RTA. Give a speed command only if you are not
        # already at the minimum speed you can fly at

        min_spd_flag = (np.abs((traf.cas - traf.perf.vmcr)) < 2.0)[idx]
        max_spd_flag = (np.abs((traf.cas - np.where(traf.alt > traf.perf.hptrans,
                                             aero.vmach2cas(traf.perf.mmo, traf.alt[idx]),
                                             traf.perf.vmo))) < 2.0)[idx]

        if (eta - tw_opening) < - tolerance and not min_spd_flag:

            cas     = self.target_speed(idx,eta,tw_opening + self.time_tolerance)
            kdesspd = self.spd_cmd(idx, cas)
            self.log_data(idx, "lower", kdesspd, tolerance)

        # if the ETA is higher than the lower bound of the time window request to meet the RTA by slowinf
        # the aircraft down.
        elif (eta - tw_closing) > tolerance and not max_spd_flag:
            cas     = self.target_speed(idx,eta, tw_closing - self.time_tolerance)
            kdesspd = self.spd_cmd(idx, cas)
            self.log_data(idx, "upper", kdesspd, tolerance)

        # if the ETA is width in the time window don't give any speed comands
        else:
            pass
            self.log_data(idx,None, None, tolerance)

    def dead_band(self,flight_time):
        """
        Function to introduce time constraint limits for the time error between ETA and required time of arrival.
        :param flight_time: remaining flight time [s].
        :return: time tolerance [s].
        """
        # Default Time tolerance (T) is 6 seconds.
        # If the remaining flight time to RTA is larger than 2h, then the T is 2min.
        time_tolerance = np.where((flight_time >= 2.0 * 60**2), 2.*60 ,self.time_tolerance)                        # [s]
        # If the remaining flight time to RTA is larger than 60 * T [min], then T is 1.667% of the flight time.
        time_tolerance = np.where((flight_time >= self.time_tolerance * 60), 1/60. * flight_time,time_tolerance)   # [s]

        return np.round(time_tolerance,1)

    def define_tw(self, idx):

        # get the RTA at the current way-point with RTA constraint
        rta_timestamp = traf.ap.route[idx].wprta[traf.ap.route[idx].iacwprta]  # required time of arrival
        # convert the RTA timestamp to seconds from simulation time
        tw_opening         = max((rta_timestamp - sim.utc).total_seconds(), 0.01)                # [s]
        tw_closing         = (rta_timestamp - sim.utc).total_seconds() + self.tw_length[idx]     # [s]

        return tw_opening,tw_closing

    @staticmethod
    def target_speed(idx,ETA,RTA):
        # Use as first estimate the average TAS required to reach the RTA time.
        # the TAS to reach the RTA is the same as flying
        tas_estimate = ETA * traf.tas[idx] / RTA
        cas_estimate = aero.tas2cas(tas_estimate,traf.alt[idx])

        return cas_estimate

    @staticmethod
    def dimensions2rta(idx):

        # calcualte the distance from current postion to the active way-point
        dist_2_nextwp = geo.latlondist(traf.lat[idx], traf.lon[idx],
                                     traf.ap.route[idx].wplat[traf.ap.route[idx].iactwp],
                                     traf.ap.route[idx].wplon[traf.ap.route[idx].iactwp]) / aero.nm # [m]

        # distances between way-points up until the active way-point with time constraint
        dist2rta = np.concatenate((np.array([dist_2_nextwp]),
                                 traf.ap.route[idx].wpdistto[
                                 traf.ap.route[idx].iactwp + 1:
                                 traf.ap.route[idx].iacwprta + 1]), axis=0) * aero.nm  # [m]

        return dist2rta

    @staticmethod
    def spd_cmd(idx, desspd):
        # Function to change the speed of the aircraft
        # Check if exceed maximum operating speed is exceeded
        desspd   = np.where((desspd < traf.perf.vmcr), traf.perf.vmcr, desspd)
        # in traf, we will check for min and max spd, hence a flag is required.
        transalt_flag = np.where(traf.alt > traf.perf.hptrans,True,False)

        if transalt_flag[idx]:
            # maximum Mach
            desspd = np.where((aero.vcas2mach(desspd, traf.alt[idx]) > traf.perf.mmo),
                              aero.vmach2cas(traf.perf.mmo, traf.alt[idx]), desspd)
        else:
            # maximum CAS: below crossover and above crossover
            desspd = np.where((desspd > traf.perf.vmo), traf.perf.vmo, desspd)

        kdesspd = desspd[idx] / aero.kts
        stack.stack(f'SPD {traf.id[idx]} {kdesspd}')
        stack.stack(f'VNAV {traf.id[idx]} ON')
        return kdesspd

    def log_data(self,idx,bound,desspd,tolerance):

        self.logger.log(
            [sim.utc.time(),traf.wind.current_ensemble,tolerance,
            traf.ap.route[idx].iactwp,
            traf.ap.route[idx].iacwprta,
            bound,
            traf.cas[idx] / aero.kts,
            desspd]
        )

