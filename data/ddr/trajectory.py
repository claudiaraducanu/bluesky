import os
import math
import pandas as pd
from bluesky import settings

class trajectory():

    def __init__(self,filename):

        file_path_trajectory = os.path.join(os.getcwd(),"data", "ddr", "data", filename)
        self.trajectory = pd.read_csv(file_path_trajectory, delimiter=',')
        self._airports   = dict()

    def initiate_aircraft(self,data):

        self._get_airports(data)

        return '0:00:00.00>CRE  KL204, A320,' + str(self._airports['ORIG']['aplat']) + ',' + \
                str(self._airports['ORIG']['aplon']) + ',0,0,1' + '\n'  \
               '0:00:00.00>ORIG KL204 ' + self._airports['ORIG']['apid'] + '\n' \
               '0:00:00.00>DEST KL204 ' + self._airports['DEST']['apid'] + '\n' \

    def get_waypoint(self,index):

        return '0:00:00.00>ADDWPT KL204 ' + str(self.trajectory['st_x(gpt.coords)'][index]) + ' ' + \
                str(self.trajectory['st_y(gpt.coords)'][index]) + ' ' + \
                'FL' + str(self.trajectory['fl'][index]) + '\n'

    def _get_airports(self,data):

        no_apt = self.trajectory[pd.Index(self.trajectory['type.1'] == 'A')].index

        if no_apt.size > 2:
            raise ValueError("Flight has a stop en-route to destination airport")
        else:

            self._airports['ORIG']  = self._index(data,type='ap', \
                                       latitude= self.trajectory['st_x(gpt.coords)'][min(no_apt)], \
                                       longitude = self.trajectory['st_y(gpt.coords)'][min(no_apt)])

            self._airports['DEST']  = self._index(data,type='ap', \
                                       latitude= self.trajectory['st_x(gpt.coords)'][max(no_apt)], \
                                       longitude = self.trajectory['st_y(gpt.coords)'][max(no_apt)])

    @staticmethod
    def _index(data, type, latitude, longitude):

        index = []
        for i in range(0, len(data[type + 'id'])):

            if math.isclose(latitude, data[type + 'lat'][i], rel_tol=0.001) & \
                    math.isclose(longitude, data[type + 'lon'][i], rel_tol=0.001):
                index.append(i)

        if len(index) != 1:
            raise ValueError("Multiple" + str(type) + " found at (longitude,latitude) ")
        elif len(index) == 0:
            raise ValueError("No" + str(type) +  "found at (longitude,latitude) ")
        else:
            return { 'index': index[0],
                      'apid' : data[type + 'id'][index[0]],
                      'aplat': data[type + 'lat'][index[0]],
                      'aplon': data[type + 'lon'][index[0]]}





