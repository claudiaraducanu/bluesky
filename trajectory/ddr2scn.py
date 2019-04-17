import os
import math
import pandas as pd
import numpy as np
from bluesky.tools import geo

class trajectories():


    def __init__(self):

        self.data   = dict()
        self.scn    = dict()

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


    def _get_waypoint(self,key,type='wpt',order=None):
        """

        :param key:
        :param type:
        :return:
        """

        if type == 'org':
            wpt = self.data[key].loc[(self.data[key]['order'] == 1)].iloc[0]
            if wpt['type.1'] is not 'A':
                raise Warning("waypoint selected for origin is not an airport")
        elif type == 'dest':
            wpt = self.data[key].loc[(self.data[key]['order'] == self.data[key]['order'].max())].iloc[0]
            if wpt['type.1'] is not 'A':
                raise Warning("waypoint selected for origin is not an airport")
        elif type == 'wpt':
            if order is None:
                raise ValueError("need to specify the waypoint number")
            else:
                wpt = self.data[key].loc[self.data[key]['order'] == order].iloc[0]
        else:
            raise ValueError("Waypoint types are limited to org/dest/wpt")

        return wpt

    def from_csv(self,filename):
        """

        :param filename: ddr2 data format filename
        :return:
        """

        data_log = pd.read_csv(filename, delimiter=',',skipinitialspace = True) # Import DDR2 data into a panda dataframe
        key = self.record_to_key(data_log.iloc[0])
        if key not in self.data:
            data_log['timestamp'] = pd.DatetimeIndex(data_log['time_over'])
            self.data[key] = data_log.drop(columns=["trajectory_id","type","time_over"])


    @staticmethod
    def _avg_spd(wpt1,wpt2):
        hdg, dist = geo.qdrdist(wpt1['st_x(gpt.coords)'],
                                wpt1['st_y(gpt.coords)'],
                                wpt2['st_x(gpt.coords)'],
                                wpt2['st_y(gpt.coords)'])

        time_lapse = pd.to_timedelta(wpt2['timestamp'] - wpt1['timestamp'], unit='s').total_seconds()
        spd = np.divide(dist, np.divide(float(time_lapse), 360))

        return spd,hdg

    def cre_command(self):

        for key in self.data:

            self.scn[key] = dict()

            key_dictionary = self.key_to_dict(key)
            origin = self._get_waypoint(key, type="org")

            spd, hdg = self._avg_spd(origin,self._get_waypoint(key, type="wpt",order=2))

            self.scn[key]['cre_function']  = '0:00:00.00>CRE ' + \
                            key_dictionary['acid'] + ',' + \
                            key_dictionary['ac_type'] + ',' + \
                            str(origin['st_x(gpt.coords)']) + ',' + \
                            str(origin['st_y(gpt.coords)']) + ',' + \
                            str(hdg) + ',' + \
                            str(origin['fl']) + ',' + \
                            str(spd) + '\n'

    def dest_command(self):

        dest_functions = []

        for key in self.data:

            key_dictionary = self.key_to_dict(key)
            destination = self._get_waypoint(key, type="dest")

            self.scn[key]['dest_function'] = '0:00:00.00>DEST ' + \
                             key_dictionary['acid'] + ' ' + \
                             str(destination['st_x(gpt.coords)']) + ' ' + \
                             str(destination['st_y(gpt.coords)']) +  '\n'


    def addwpt_command(self):
        """
        Add waypoints from the ddr file
        :return:
        """


        for key in self.data:

            key_dictionary = self.key_to_dict(key)
            wpt_functions = []

            # Loop through all points in DDR2 trajectory exept for the first and last
            for i in range(2,len(self.data[key])-1):
                record = self._get_waypoint(key,type='wpt',order=i)

                wpt_functions.append('0:00:00.00>ADDWPT ' + \
                             key_dictionary['acid'] + ' ' + \
                             str(record['st_x(gpt.coords)']) + ' ' + \
                             str(record['st_y(gpt.coords)']) +  ' ' + \
                             str(record['fl']) + '00' + '\n')

            self.scn[key]['addwpt_functions'] = wpt_functions

    # def spd_command(self):
    #
    #     spd_functions =  dict()
    #
    #     for key in self.data:
    #
    #         key_dictionary = self.key_to_dict(key)
    #         wpt_functions = []
    #
    #         # Loop through all points in DDR2 trajectory exept for the first and last
    #         for i in range(2,len(self.data[key])-1):
    #             spd,hdg = self._avg_spd(self._get_waypoint(key,type='wpt',order=i),
    #                                     self._get_waypoint(key, type='wpt', order=i+1))
    #
    #             wpt_functions.append((i,'0:00:00.00>SPD ' + \
    #                          key_dictionary['acid'] + ' ' + \
    #                          str(np.round(spd,decimals=2)) + '\n'
    #
    #         spd_functions[key] = pd.DataFrame(wpt_functions,columns=['wpt_order','addwpt_function'])
    #         spd_functions[key] = addwpt_functions[key].set_index('wpt_order')
    #     return spd_functions
    #