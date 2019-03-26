import os
import math
import pandas as pd
import numpy as np
from bluesky.tools import geo

class trajectories():


    def __init__(self):

        self.data   = dict()

    @staticmethod
    def record_to_key(record):

        acid = 'F' + str(record['trajectory_id']) # Get aircraft acid
        if math.isnan(record['type']): # Get aircraft type
            ac_type = "A320"
        else:
            ac_type = record['type']

        date = record['time_over'].split()[0] # Get aircraft day of operation

        return acid + '.' + \
               ac_type + '.' + \
               date


    @staticmethod
    def key_to_dict(key):

        data = key.split(".")
        key_dictionary = dict()

        key_dictionary['acid'] = data[0]
        key_dictionary['ac_type'] = data[1]
        key_dictionary['date'] = data[2]

        return key_dictionary

    def _find_airport(self,key,type="org"):
        """

        :param key:
        :param type:
        :return:
        """

        if type == "org":
            return self.data[key].loc[(self.data[key]['type.1'] == "A")
                                     & (self.data[key]['order'] == 1)].iloc[0]
        elif type == "dest":

            return self.data[key].loc[(self.data[key]['type.1'] == "A")
                                          & (self.data[key]['order'] == self.data[key]['order'].max())].iloc[0]
        else:
            ValueError("Not a valid airport type")

    def _get_waypoint(self,key,order):
        """

        :param key:
        :param order:
        :return:
        """

        if type(order) == int:
            return self.data[key].loc[self.data[key]['order'] == order].iloc[0]
        else:
            TypeError("Order must be an integer")

    def from_csv(self,filename):

        data_log = pd.read_csv(filename, delimiter=',',skipinitialspace = True) # Import DDR2 data into a panda dataframe
        key = self.record_to_key(data_log.iloc[0])
        if key not in self.data:
            data_log['timestamp'] = pd.DatetimeIndex(data_log['time_over'])
            self.data[key] = data_log.drop(columns=["trajectory_id","type","time_over"])

    def initiate_aircraft(self):

        cre_functions = []

        for key in self.data:

            key_dictionary = self.key_to_dict(key)
            origin = self._find_airport(key,type="org")
            hdg,dist = geo.qdrdist(origin['st_x(gpt.coords)'],
                                    origin['st_y(gpt.coords)'],
                                    self._get_waypoint(key,2)['st_x(gpt.coords)'],
                                    self._get_waypoint(key,2)['st_y(gpt.coords)'])

            timelapse = pd.to_timedelta(self._get_waypoint(key, 2)['timestamp'] - origin['timestamp'],unit='s').total_seconds()
            spd = np.divide(dist,np.divide(float(timelapse),360))

            cre_functions.append('0:00:00.00>CRE ' + \
                                    key_dictionary['acid'] + ',' + \
                                    key_dictionary['ac_type'] + ',' + \
                                    str(origin['st_x(gpt.coords)']) + ',' + \
                                    str(origin['st_y(gpt.coords)']) + ',' + \
                                    str(hdg) + ',' + \
                                    str(origin['fl']) + ',' + \
                                    str(spd) + '\n')


        return cre_functions

    def add_destination(self):

        dest_functions = []

        for key in self.data:

            key_dictionary = self.key_to_dict(key)
            destination = self._find_airport(key, type="dest")

            dest_functions.append('0:00:00.00>DEST ' + \
                             key_dictionary['acid'] + ' ' + \
                             str(destination['st_x(gpt.coords)']) + ' ' + \
                             str(destination['st_y(gpt.coords)']) +  '\n')

        return dest_functions

    def add_all_wpt(self):


        addwpt_functions =  dict()

        for key in self.data:

            key_dictionary = self.key_to_dict(key)
            wpt_functions = []

            # Loop through all points in DDR2 trajectory exept for the first and last
            for i in range(2,len(self.data[key])-1):
                record = self._get_waypoint(key,i)

                wpt_functions.append((i,'0:00:00.00>ADDWPT ' + \
                             key_dictionary['acid'] + ' ' + \
                             str(record['st_x(gpt.coords)']) + ' ' + \
                             str(record['st_y(gpt.coords)']) +  ' ' + \
                             str(record['fl']) + '00' + '\n'))

            addwpt_functions[key] = pd.DataFrame(wpt_functions,columns=['wpt_order','addwpt_function'])

        return addwpt_functions
