""" BlueSky deletion area plugin. This plugin can use an area definition to
    delete aircraft that exit the area. Statistics on these flights can be
    logged with the FLSTLOG logger. """
import numpy as np
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import traf, sim  #, settings, navdb, traf, sim, scr, tools
from bluesky.tools import datalog, areafilter, \
    TrafficArrays, RegisterElementParameters
from bluesky.tools.aero import ft
from bluesky import settings

# Log parameters for the flight statistics log
header = \
    "#######################################################\n" + \
    "FUEL LOG\n" + \
    "Flight Statistics\n" + \
    "#######################################################\n\n" + \
    "Parameters [Units]:\n" + \
    "Deletion Time [s], " + \
    "Call sign [-], " + \
    "Spawn Time [s], " + \
    "Deletion Mass [kg], " + \
    "Initial Mass [kg]"  + "\n"

# Global data
logger = None
# List of aircraft that are being logged
flights = list()

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():

    # Addtional initilisation code
    global logger,flights
    logger = datalog.crelog('FUEL',None,header)
    flights = list()

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'FUELLOG',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim',

        # Update interval in seconds.
        'update_interval': 0.5,

        # The update function is called after traffic is updated.
        'update':          update(),
        }

    stackfunctions = {
        "FUELLOG": [
            "FUELLOG LIST OR ADD sectorname or REMOVE sectorname",
            "txt,[txt]",
            log_info,
            "Add/remove/list sectors for occupancy count"
        ]
    }
    # init_plugin() should always return these two dicts.
    return config, stackfunctions


def update():

    logger.log("Hello")
    # ''' Update flight efficiency metrics
    #     2D and 3D distance [m], and work done (force*distance) [J] '''
    # if self.swtaxi and not self.active:
    #     return
    #
    # resultantspd = np.sqrt(traf.gs * traf.gs + traf.vs * traf.vs)
    # self.distance2D += self.dt * traf.gs
    # self.distance3D += self.dt * resultantspd
    #
    # if settings.performance_model == 'openap':
    #     self.work += (traf.perf.thrust * self.dt * resultantspd)
    # else:
    #     self.work += (traf.perf.Thr * self.dt * resultantspd)
    #
    # # Autodelete for descending with swTaxi:
    # if not self.swtaxi:
    #     #delidxalt = np.where(traf.alt<self.swtaxialt)[0]
    #     delidxalt = np.where((self.oldalt>=self.swtaxialt)*(traf.alt<self.swtaxialt))[0]
    #     self.oldalt = traf.alt
    # else:
    #     delidxalt = []
    #
    #
    #
    # # Find out which aircraft are currently inside the experiment area, and
    # # determine which aircraft need to be deleted.
    # inside = areafilter.checkInside(self.name, traf.lat, traf.lon, traf.alt)
    # #delidx = np.intersect1d(np.where(np.array(self.inside)==True), np.where(np.array(inside)==False))
    # delidx = np.where(np.array(self.inside)*(np.array(inside) == False))[0]
    # self.inside = inside

    # Log flight statistics when for deleted aircraft
    # if len(delidx) > 0:
    #     self.logger.log(
    #         np.array(traf.id)[delidx],
    #         self.create_time[delidx],
    #         sim.simt - self.create_time[delidx],
    #         self.distance2D[delidx],
    #         self.distance3D[delidx],
    #         self.work[delidx],
    #         traf.lat[delidx],
    #         traf.lon[delidx],
    #         traf.alt[delidx],
    #         traf.tas[delidx],
    #         traf.vs[delidx],
    #         traf.hdg[delidx],
    #         # traf.ap.origlat[delidx],
    #         # traf.ap.origlon[delidx],
    #         # traf.ap.destlat[delidx],
    #         # traf.ap.destlon[delidx],
    #         traf.asas.active[delidx],
    #         traf.pilot.alt[delidx],
    #         traf.pilot.tas[delidx],
    #         traf.pilot.vs[delidx],
    #         traf.pilot.hdg[delidx]
    #     )
    #     # delete all aicraft in self.delidx
    #     traf.delete(delidx)
    #
    #
    # # delete all aicraft in self.delidxalt
    # if len(delidxalt)>0:
    #     traf.delete(list(delidxalt))

def log_info(type,aircraft_id):
    ''' Set information to log. Aicraft reaching their destination airport are deleted.'''

    # start by checking if the first argument is a string -> then it is an area name
    if type=="LIST":
        return True, "Aircraft that are being logged: " + str.join(', ', flights)
    elif type=="ADD":
        if aircraft_id in traf.id: # Check if aircraft to be added is in simulation
            if aircraft_id not in flights:
                if len(flights) == 0:
                    logger.start()
                return True, "Flight" + str(aircraft_id) + "added to list of logged aircraft"
            else:
                return False, "Flight" + str(aircraft_id) + " id already in the list of logged aircraft"
    else:
        if aircraft_id in flights: # Check if aircraft to be added is in simulation
            # Remove area from flight list
            idx = flights.index(id)
            flights.pop(idx)
            return True, 'Flight' + str(id) + 'is removed from  list.'
        else:
            return False, "No flight registered with id "  + str(id)