""" Flight Management System Mode plugin """
# Import the global bluesky objects. Uncomment the ones you need
from datetime import datetime
from plugins.patch_route import patch_route
# from math import sqrt
import numpy as np

from bluesky import sim, stack, traf
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
        self.dt                                     = 30.0      # [s] frequency of AFMS update
        self.thrcontrol                             = 6.0       # [s]
        self.switchwp                               = 60.0      # [s]
        # Path the route class with some extra default variables to store route information associate to time windows
        patch_route()

        with RegisterElementParameters(self):
            self.afmsOn               = np.array([],dtype = np.bool) # AFMS on or off
            self.twlength             = np.array([])

    def create(self, n=1):
        super(Afms, self).create(n)
        self.afmsOn[-n:]      = False
        self.twlength[-n:]    = 0

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

            self.twlength[idx] = tw_size

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

                self.logger = datalog.crelog('FMSLOG', None, header=" ")
                self.logger.start()

                return True, "AFMS is currently active for  " + traf.id[idx]

            elif not onoff:
                # add the aircraft to the list of aircraft with advanced fms mode on
                self.afmsOn[idx] = onoff
                self.logger.reset()

            else:
                return False, "Unknown argument!"

    def update(self):

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
                    """ Determine if the active way-point with RTA should still be followed,
                     or switch to the next way-point """

                    """Calculate the ETA at the way-point with rta and the 
                     maximum and minimum required time of arrival based on time window length  """

                    """" Estimated time of arrival at the middle of the time window"""
                    # distances between way-points up until the active way-point with RTA
                    distto          = self.distorta(idx)  # [m]

                    # flight levels at each way-point between current position and the activate way-point with RTA
                    flightlevels    = self.fl2rta(idx)  # [m]

                    """ Determine whether with the current CAS you reach the RTA and time window"""
                    ETAcurrent = self.eta2rta(traf.cas[idx], distto,
                                              flightlevels)  # [s] calculated estimated time of

                    self.logger.log(sim.utc.time(),
                                    traf.ap.route[idx].iactwp,
                                    traf.ap.route[idx].iacwprta,
                                    ETAcurrent
                                    )

                    # if traf.ap.route[idx].iacwprta < traf.ap.route[idx].iactwp and ETAcurrent < 300:
                    if ETAcurrent < self.switchwp and len(traf.ap.route[idx].rta):

                        # earli
                        traf.ap.route[idx].iacwprta = traf.ap.route[idx].rta[0]
                        # remove the active rta from the list
                        traf.ap.route[idx].rta = traf.ap.route[idx].rta[1:]

                        """" Estimated time of arrival at the middle of the time window"""
                        # distances between way-points up until the active way-point with RTA
                        distto = self.distorta(idx)  # [m]

                        # flight levels at each way-point between current position and the activate way-point with RTA
                        flightlevels = self.fl2rta(idx)  # [m]

                        """ Determine whether with the current CAS you reach the RTA and time window"""
                        ETAcurrent = self.eta2rta(traf.cas[idx], distto,
                                                  flightlevels)  # [s] calculated estimated time of

                    else:
                        pass

                    # get the RTA at the current way-point with RTA constraint
                    rtaTime = traf.ap.route[idx].wprta[traf.ap.route[idx].iacwprta]  # required time of arrival

                    # convert the RTA timestamp to seconds from simulation time
                    rta       = max((rtaTime - sim.utc).total_seconds(),0)  # [s]

                    if rta:
                        upper_rta = (rtaTime - sim.utc).total_seconds() + self.twlength[idx]             # [s]
                    else:
                        upper_rta = self.twlength[idx]

                    # There must be some tolerance between the ETA and RTA to minimize throttle activity.
                    if    (ETAcurrent - rta) < - self.thrcontrol:
                        cas = self.cas2rta(distto, flightlevels,  rta)
                        self.spdCmd(idx,cas,flightlevels)
                        self.logger.log(sim.utc.time(),rtaTime.time(),
                                        traf.ap.route[idx].iactwp,
                                        traf.ap.route[idx].iacwprta,
                                        ETAcurrent,rta,upper_rta,
                                        (ETAcurrent - rta) < - self.thrcontrol,
                                        (ETAcurrent - upper_rta) > self.thrcontrol,
                                        traf.gs[[idx]],
                                        traf.tas[[idx]],
                                        traf.cas[[idx]],
                                        cas)

                    # if the ETA is higher than the lower bound of the time window request to meet the RTA by slowinf
                    # the aircraft down.
                    elif  (ETAcurrent - upper_rta) > self.thrcontrol:
                        cas = self.cas2rta(distto, flightlevels,  upper_rta)
                        self.spdCmd(idx,cas,flightlevels)
                        self.logger.log(sim.utc.time(),rtaTime.time(),
                                        traf.ap.route[idx].iactwp,
                                        traf.ap.route[idx].iacwprta,
                                        ETAcurrent,rta,upper_rta,
                                        (ETAcurrent - rta) < - self.thrcontrol,
                                        (ETAcurrent - upper_rta) > self.thrcontrol,
                                        traf.gs[[idx]],
                                        traf.tas[[idx]],
                                        traf.cas[[idx]],cas)

                    # if the ETA is width in the time window don't give any speed comands
                    else:
                        self.logger.log(sim.utc.time(),rtaTime.time(),
                                        traf.ap.route[idx].iactwp,
                                        traf.ap.route[idx].iacwprta,
                                        ETAcurrent,rta,upper_rta,
                                        (ETAcurrent - rta) < - self.thrcontrol,
                                        (ETAcurrent - upper_rta) > self.thrcontrol,
                                        traf.gs[[idx]],
                                        traf.tas[[idx]],
                                        traf.cas[[idx]],0)


    def cas2rta(self,distto,flightlevels,rta):
        # Use as first estimate the average TAS required to reach the RTA time.
        #
        TASestimate = np.divide(np.sum(distto), rta)  # initial guess is current speed [m/s]
        CASestimate = aero.tas2cas(TASestimate, flightlevels[0])  # convert TAS to CAS
        eta         = self.eta2rta(CASestimate, distto, flightlevels)  # calculated estimated time of arrival

        while abs(eta - rta) > 0.1:
            prevTASestimate = TASestimate
            # the TAS to reach the RTA is the same as flying
            TASestimate = eta * prevTASestimate / rta

            CASestimate = aero.tas2cas(TASestimate, flightlevels[0])
            eta         = self.eta2rta(CASestimate, distto, flightlevels)

        return CASestimate

    def spdCmd(self, idx, cas, flightlevels):
        # Function to change the speed of the aircraft

        if abs(traf.cas[idx] - cas) > aero.kts:  # Don't give very small speed changes

            if abs(traf.vs[idx]) < 2.5:  # Don't give a speed change when changing altitude
                if aero.cas2mach(cas, flightlevels[0]) > traf.perf.mmo[idx]:
                    stack.stack(f'SPD {traf.id[idx]} {traf.perf.mmo[idx]}')
                if cas < traf.perf.vmcr[idx]:
                    stack.stack(f'SPD {traf.id[idx]} {traf.perf.vmcr[idx]/aero.kts}')

                elif flightlevels[0] > 7620.:#traf.perf.hpdes:
                    stack.stack(f'SPD {traf.id[idx]}, {aero.cas2mach(cas, flightlevels[0])}')

                else:
                    stack.stack(f'SPD {traf.id[idx]}, {cas / aero.kts}')
                stack.stack(f'VNAV {traf.id[idx]} ON')

        else:
            pass

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

    @staticmethod
    def distorta(idx):
        # calcualte the distance from current postion to the active way-point
        _, dist2nextwp = geo.qdrdist(traf.lat[idx], traf.lon[idx],
                                     traf.ap.route[idx].wplat[traf.ap.route[idx].iactwp],
                                     traf.ap.route[idx].wplon[traf.ap.route[idx].iactwp])  # [nm]

        # distances between way-points up until the active way-point with RTA
        distto = np.concatenate((np.array([dist2nextwp]),
                                 traf.ap.route[idx].wpdistto[
                                 traf.ap.route[idx].iactwp + 1:
                                 traf.ap.route[idx].iacwprta + 1]), axis=0) * aero.nm  # [m]

        return distto

    @staticmethod
    def fl2rta(idx):
        # flight levels at each way-point between current position and the activate way-point with RTA. Assume
        # instantaneous flight level change. 
        flightlevels = np.concatenate((np.array([traf.alt[idx]]),
                                       traf.ap.route[idx].wpalt[
                                       traf.ap.route[idx].iactwp + 1:
                                       traf.ap.route[idx].iacwprta + 1]), axis=0)

        return flightlevels


