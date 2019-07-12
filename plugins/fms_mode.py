""" Flight Management System Mode plugin """
# Import the global bluesky objects. Uncomment the ones you need
from datetime import date, datetime, time, timedelta
from plugins.patch_route import patch_route
# from math import sqrt
import numpy as np

from bluesky import sim, stack, traf, tools  #, settings, navdb, sim, scr, tools
from bluesky.tools import aero,geo,TrafficArrays, RegisterElementParameters
from bluesky.traffic.route import Route
from bluesky.traffic.performance.legacy.performance import PHASE

# Global data
afms = None

def init_plugin():

    # Additional initilisation code
    global afms, acceleration_m_s2, deceleration_m_s2
    acceleration_m_s2 = 0.5
    deceleration_m_s2 = -0.5

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
        self.dt                                     = 60.0    # [s] frequency of AFMS update
        self.skip2nwp                               = 300.0   # [s] sw
        # Path the route class with some extra default variables to store route information associate to time windows
        patch_route()

        with RegisterElementParameters(self):
            self.afmsOn      = np.array([],dtype = np.bool) # AFMS on or off
            self.rtaTime     = np.array([])                 # current active way-point with RTA

    def create(self, n=1):
        super(Afms, self).create(n)
        self.afmsOn[-n:]    = False

    def set_rta(self,*args):

        if len(args) != 6:
            return False, 'RTA function requires 6 arguments acid, wpname,day,month,year,HH:MM:SS'
        else:

            idx,name,day,month,year,wprtatime  = args[0],args[1],args[2],args[3],args[4],args[5]

            # make sure that the way-point exists
            if name in traf.ap.route[idx].wpname:

                wpidx = traf.ap.route[idx].wpname.index(name)
                traf.ap.route[idx].wprta[wpidx] = datetime.strptime(
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

            # convert to array the tw size at each way-point in order to use indexing
            arrayWpTw = np.array(traf.ap.route[idx].wptw)

            # change the time window size from default for way-points with rta constraint
            arrayWpTw[traf.ap.route[idx].rta] = tw_size

            # convert back to list
            traf.ap.route[idx].wptw = list(arrayWpTw)

            return True, traf.id[idx] + " time window length set for " + str(tw_size) + " seconds"

    def set_mode(self, *args):

        if len(args) != 2:
            return False, 'AFMS needs 2 arguments'
        else:

            idx,onoff = args[0], args[1]

            if  onoff:
                # add the aircraft to the list of aircraft with advanced fms mode on
                self.afmsOn[idx] = onoff
                # sort the way-points with RTA in the order in which they are encountered in route
                traf.ap.route[idx].rta.sort()

                # set the current active way-point with RTA to the first element in the way-points with RTA list
                traf.ap.route[idx].iacwprta     = traf.ap.route[idx].rta[0]
                # remove the active rta from the list
                traf.ap.route[idx].rta          = traf.ap.route[idx].rta[1:]

                return True, "AFMS is currently active for  " + traf.id[idx]

            elif not onoff:
                # add the aircraft to the list of aircraft with advanced fms mode on
                self.afmsOn[idx] = onoff

            else:
                return False, "Unknown argument!"

    def update(self):  #
        pass

    def reset(self):  #
        pass

    def preupdate(self):

        # check if for any aircraft the AFMS mode is active
        if not self.afmsOn.any():
            pass
        else:
            afmsIds = np.where(self.afmsOn)[0]

            for idx in afmsIds:
                if int(traf.perf.phase[idx]) != PHASE['CR']:
                    pass

                else:

                    """Calculate the required time of arrival to reach the middle of the time window and the 
                     maximum and minimum required time of arrival based on time window length  """

                    # get the RTA and TW length at the current way-point with RTA constraint
                    rtaTime  = traf.ap.route[idx].wprta[traf.ap.route[idx].iacwprta] # required time of arrival
                    tw       = traf.ap.route[idx].wptw[traf.ap.route[idx].iacwprta]  # [s] time window length

                    # convert the RTA timestamp to seconds from simulation time
                    rtaSimt = (rtaTime - sim.utc).total_seconds() # [s]

                    # If the time of arrival in the middle of the way-point is

                    # get the earliest arrival time within the time window
                    lower_rtaSimt = max(rtaSimt - tw/2, 0)
                    # get the latest arrival time within the time window
                    upper_rtaSimt = max(rtaSimt + tw/2, 0)


                    """" Estimated time of arrival at the middle of the time window"""

                    # calcualte the distance from current postion to the active way-point
                    _, dist2nextwp = geo.qdrdist(traf.lat[idx], traf.lon[idx],
                                                    traf.ap.route[idx].wplat[traf.ap.route[idx].iactwp],
                                                    traf.ap.route[idx].wplon[traf.ap.route[idx].iactwp])        # [nm]

                    # distances between way-points up until the active way-point with RTA
                    distto         = np.concatenate((np.array([dist2nextwp]),
                                                            traf.ap.route[idx].wpdistto[
                                                            traf.ap.route[idx].iactwp+1:
                                                            traf.ap.route[idx].iacwprta+1]),axis=0) * aero.nm   # [m]

                    # flight levels at each way-point between current position and the activate way-point with RTA
                    flightlevels   = np.concatenate((np.array([traf.alt[idx]]),
                                                    traf.ap.route[idx].wpalt[
                                                    traf.ap.route[idx].iactwp + 1 :
                                                    traf.ap.route[idx].iacwprta +1]),axis=0)                   # [m]


                    """ Determine the CAS required to reach the RTA  """

                    # Use as first estimate the TAS calculated using the distance divided by RTA time

                    TASestimate        = traf.tas[idx] # initial guess is current speed [m/s]
                    CASestimate        = traf.cas[idx]
                    CASestimatePrev    = 0

                    while abs(CASestimate - CASestimatePrev) > 0.1:

                        # Compute the time to accelerate or decelerate to the new TAS
                        delta_spd   = TASestimate - traf.tas[idx] # [m/s]
                        need_ax     = np.abs(delta_spd) > aero.kts  # small threshold
                        ax          = need_ax * np.sign(delta_spd) * traf.perf.acceleration()       # [m/s^2]

                        if ax != 0:
                            accTime     = np.divide(delta_spd,ax) # [s]
                        else:
                            accTime = 0.0

                        # Calculate the ETA including the time it takes to accelerate
                        ETAestimate     = self.eta2rta(CASestimate, distto, flightlevels) - accTime  #[s]
                        # Save the previous

                        CASestimatePrev  = CASestimate

                        CASestimate      = CASestimate * ETAestimate / rtaSimt
                        TASestimate  =  aero.cas2tas(CASestimate,flightlevels[0])

                    iterations = 4
                    estimated_cas = traf.cas[idx]
                    for i in range(iterations):

                        total_time_s = self.eta2rta(estimated_cas,distto,flightlevels)  - \
                                       self._dtime2new_cas(flightlevels[0], traf.cas[idx], estimated_cas)
                        if total_time_s < 0:
                            estimated_time2rta_s = 0.0
                        else:
                            estimated_time2rta_s = total_time_s

                        previous_estimate_m_s = estimated_cas
                        estimated_cas = estimated_cas* estimated_time2rta_s / (rtaSimt+ 0.00001)
                        if abs(previous_estimate_m_s - estimated_cas) < 1:
                            break
                    return estimated_cas    #
    #                 if time_s2rta < self.skip2next_rta_time_s:
    #                     pass
    #                 else:
    #                     _, dist2nwp = tools.geo.qdrdist(traf.lat[idx], traf.lon[idx],
    #                                                     traf.ap.route[idx].wplat[rta_init_index],
    #                                                     traf.ap.route[idx].wplon[rta_init_index])
    #                     distances_nm = np.concatenate((np.array([dist2nwp]),
    #                                                 traf.ap.route[idx].wpdistto[rta_init_index + 1:rta_last_index + 1]),
    #                                                axis=0)
    #                     flightlevels_m = np.concatenate((np.array([traf.alt[idx]]),
    #                                                    traf.ap.route[idx].wpalt[rta_init_index + 1:rta_last_index + 1]))
    #                     # rta_cas_kts = self._rta_cas_wfl(distances_nm, flightlevels_m, time_s2rta, traf.cas[idx]) * 3600 / 1852
    #                     rta_cas_m_s = self._cas2rta(distances_nm, flightlevels_m, time_s2rta, traf.cas[idx])
    #
    #
    #                     if abs(traf.cas[idx] - rta_cas_m_s) > 0.5:  # Don't give very small speed changes
    #                         if abs(traf.vs[idx]) < 2.5:  # Don't give a speed change when changing altitude
    #                             if tools.aero.vcas2mach(rta_cas_m_s, flightlevels_m[0]) > 0.95:
    #                                 stack.stack(f'SPD {traf.id[idx]}, {0.95}')
    #                             elif flightlevels_m[0] > 7620:
    #                                 stack.stack(f'SPD {traf.id[idx]}, {tools.aero.vcas2mach(rta_cas_m_s, flightlevels_m[0])}')
    #                             else:
    #                                 stack.stack(f'SPD {traf.id[idx]}, {rta_cas_m_s * 3600 / 1852}')
    #                             stack.stack(f'VNAV {traf.id[idx]} ON')
    #                     else:
    #                         pass
    #             elif fms_mode == 4:  # AFMS_MODE TW
    #                 rta_init_index, rta_last_index, rta = self._current_rta(idx)
    #                 tw_init_index, tw_last_index, tw_size = self._current_tw_size(idx)
    #                 time_s2rta = self._time_s2rta(rta)
    #
    #                 _, dist2nwp = tools.geo.qdrdist(traf.lat[idx], traf.lon[idx],
    #                                                 traf.ap.route[idx].wplat[rta_init_index],
    #                                                 traf.ap.route[idx].wplon[rta_init_index])
    #                 distances_nm = np.concatenate((np.array([dist2nwp]),
    #                                             traf.ap.route[idx].wpdistto[rta_init_index + 1:rta_last_index + 1]),
    #                                            axis=0)
    #                 flightlevels_m = np.concatenate((np.array([traf.alt[idx]]),
    #                                                traf.ap.route[idx].wpalt[rta_init_index + 1:rta_last_index + 1]))
    #
    #                 # Calculate Preferred Speed and Preferred Time of Arrival
    #                 own_spd = self._current_own_spd(idx)
    #                 if own_spd < 0:
    #                     # No speed specified.
    #                     if traf.selspd[idx] > 0:  # Use selected speed
    #                         _, preferred_cas_m_s, _ = tools.aero.vcasormach(traf.selspd[idx], traf.alt[idx])
    #                     else:  # Use current speed
    #                         preferred_cas_m_s = traf.cas[idx]
    #                 else:
    #                     _, preferred_cas_m_s, _ = tools.aero.vcasormach(own_spd, traf.alt[idx])
    #
    #                 eta_s_preferred = self._eta2tw_cas_wfl(distances_nm, flightlevels_m, preferred_cas_m_s)
    #
    #                 # Jump to next +1 waypoint when close to next waypoint
    #                 if eta_s_preferred < self.skip2next_rta_time_s:
    #                     rta_init_index, rta_last_index, rta = self._current_rta_plus_one(idx)
    #                     #Don't change the time window size yet. Keep the current window size
    #                     time_s2rta = self._time_s2rta(rta)
    #                     _, dist2nwp = tools.geo.qdrdist(traf.lat[idx], traf.lon[idx],
    #                                                     traf.ap.route[idx].wplat[rta_init_index],
    #                                                     traf.ap.route[idx].wplon[rta_init_index])
    #                     distances_nm = np.concatenate((np.array([dist2nwp]),
    #                                                 traf.ap.route[idx].wpdistto[rta_init_index + 1:rta_last_index + 1]),
    #                                                axis=0)
    #                     flightlevels_m = np.concatenate((np.array([traf.alt[idx]]),
    #                                                    traf.ap.route[idx].wpalt[rta_init_index + 1:rta_last_index + 1]))
    #
    #                     eta_s_preferred = self._eta2tw_cas_wfl(distances_nm, flightlevels_m, preferred_cas_m_s)
    #                 else:
    #                     pass
    #
    #                 earliest_time_s2rta = max(time_s2rta - tw_size/2, 0)
    #                 latest_time_s2rta = max(time_s2rta + tw_size/2, 0)
    #
    #                 if eta_s_preferred < earliest_time_s2rta:  # Prefer earlier then TW
    #                     time_window_cas_m_s = self._cas2rta(distances_nm, flightlevels_m, earliest_time_s2rta,
    #                                                         traf.cas[idx])
    #                 elif eta_s_preferred > latest_time_s2rta:  # Prefer later then TW
    #                     time_window_cas_m_s = self._cas2rta(distances_nm, flightlevels_m, latest_time_s2rta,
    #                                                         traf.cas[idx])
    #                 else:
    #                     time_window_cas_m_s = preferred_cas_m_s
    #
    #                 if abs(traf.cas[idx] - time_window_cas_m_s) > 0.5:  # Don't give very small speed changes
    #                     if abs(traf.vs[idx]) < 2.5:  # Don't give a speed change when changing altitude
    #                         if tools.aero.vcas2mach(time_window_cas_m_s, flightlevels_m[0]) > 0.95:
    #                             stack.stack(f'SPD {traf.id[idx]}, {0.95}')
    #                         elif flightlevels_m[0] > 7620:
    #                             stack.stack(f'SPD {traf.id[idx]}, {tools.aero.vcas2mach(time_window_cas_m_s, flightlevels_m[0])}')
    #                         else:
    #                             stack.stack(f'SPD {traf.id[idx]}, {time_window_cas_m_s * 3600 / 1852}')
    #                         stack.stack(f'VNAV {traf.id[idx]} ON')
    #                 else:
    #                     pass
    #             else:
    #                 return False, 'AFMS mode does not exist' + traf.id[idx]
    #         else:
    #             pass

    @staticmethod
    def eta2rta(currentCAS,distto,flightlevels):
        # Assumption is instantaneous climb to next flight level, and instantaneous speed change at new
        # flight level. Calculate the time when flying with the current CAS between way-points up until
        # the active way-point with RTA.
        currentCASschedule = np.array([currentCAS] * flightlevels.size)         # [m/s]
        currentTASschedule = aero.vcas2tas(currentCASschedule, flightlevels)    # [m/s]

        timeto          = np.divide(distto, currentTASschedule)                 # [s]
        estimatedETA    = np.sum(timeto)                                        # [s]

        return estimatedETA

