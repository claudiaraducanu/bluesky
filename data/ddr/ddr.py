from bluesky.navdatabase.loadnavdata import load_navdata
from data.ddr.trajectory import trajectory

file_name_trajectory   = "Flight_1.csv"
flight1                = trajectory(file_name_trajectory)

wptdata, aptdata, awydata, firdata, codata, rwythresholds = load_navdata()

with open("scenario/flight1.scn",'w') as scenario:
    scenario.write('0:00:00.00>ASAS ON \n')
    scenario.write(flight1.initiate_aircraft(aptdata))
    for location in range(1, max(flight1.trajectory.index) - 1):
        scenario.write(flight1.get_waypoint(location))
    scenario.write('0:00:00.00>VNAV KL204 ON \n')


# def dd2dms(decimaldegree):
#     if isinstance(decimaldegree, float) or isinstance(decimaldegree, int):
#         degree = int(decimaldegree)
#         convert = (decimaldegree - degree) * 60
#         minutes = abs(int(round(convert)))
#         seconds = abs(int(round((convert - int(convert)) * 60)))
#     else:
#         raise TypeError("Expected input to be a decimal degree")
#
#     return degree, minutes, seconds

# aptdata['aplat_degree'] = np.empty(aptdata['aplat'].size)
# aptdata['aplat_minute'] = np.empty(aptdata['aplat'].size)
# aptdata['aplat_second'] = np.empty(aptdata['aplat'].size)
#
# aptdata['aplon_degree'] = np.empty(aptdata['aplon'].size)
# aptdata['aplon_minute'] = np.empty(aptdata['aplon'].size)
# aptdata['aplon_second'] = np.empty(aptdata['aplon'].size)
#
# for i in range(0,aptdata['aplat'].size):
#     dms_lat = dd2dms(aptdata['aplat'][i])
#
#     aptdata['aplat_degree'][i] = dms_lat[0]
#     aptdata['aplat_minute'][i] = dms_lat[1]
#     aptdata['aplat_second'][i] = dms_lat[2]
#
#     dms_lon = dd2dms(aptdata['aplon'][i])
#
#     aptdata['aplon_degree'][i] = dms_lon[0]
#     aptdata['aplon_minute'][i] = dms_lon[1]
#     aptdata['aplon_second'][i] = dms_lon[2]
#
# airportdata = pd.DataFrame(aptdata)
#
#
# """ Convert airport coordinates to dms"""
# airports = trajectory[pd.Index(trajectory['type.1'] == 'A')]
# d_aplat = dd2dms(round(airports['st_x(gpt.coords)'][0],3)) # checked and its ok
# d_aplon = dd2dms(round(airports['st_y(gpt.coords)'][0],3))
# """Find airport ICAO code from database """
#
# filter_degree = airportdata[(airportdata.aplon_degree == d_aplon[0]) & (airportdata.aplat_degree == d_aplat[0])]
#
# filter_minutes = filter_degree[(math.isclose(filter_degree.aplon_minute,d_aplon[1],rel_tol=1))
#                                & (math.isclose(filter_degree.aplat_minute,d_aplat[1],rel_tol=1))]


