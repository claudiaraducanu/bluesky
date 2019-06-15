"""
This module converts the DDR2 files to Bluesky scenario file format.

Created by: Claudia Raducanu
Date: 5.03.2019
"""
import os
import pandas as pd
from bluesky.tools import aero, geo
import numpy as np

class FlightPlan():


    def __init__(self,fpath,cruise=False):
        """

        :param fpath: Complete path of file which contains trajectory data in ddr format. The file type has to
        either be .csv or .xlsx and the filename must be the aircraft acid code (e.g. ADH931.csv)
        :param cruise: True, if only cruise trajectory way-points are selected ( FL >= FL150), False if all way-points
        from origin to destination are to be included.
        """

        self.data = self._import_data(fpath,cruise)
        self.acid = fpath.split("/")[-1].split(".")[0] # get the acid from file title
        self.date_start = self.data.iloc[0].time_over # date on which flight takes place
        self.date_end = self.data.iloc[-1].time_over # date on which flight takes place
        self.ac_type = self.data.iloc[0].ac_type # type of ac that executes trajectory

    @staticmethod
    def _import_data(fpath,cruise):
        """

        :param fpath: Complete path of file which contains trajectory data in ddr format. The file type has to
        either be .csv or .xlsx and the filename must be the aircraft acid code (e.g. ADH931.csv)
        :return:  Pandas data frame of trajectory way-points

        """
        fextension = os.path.splitext(fpath)[1]  # get file extension from filepath

        # use appropriate import function depending on the file extension

        if fextension == ".csv":
            data = pd.read_csv(fpath, delimiter=',', skipinitialspace=True)  # Import DDR2 data into a panda dataframe

        elif fextension == ".xlsx":
            with open(fpath, 'rb') as excel_sheet:
                data = pd.read_excel(excel_sheet)
        else:
            raise ValueError("file extension must be either .csv or .xlsx")

        # Convert the time over waypoint from string to a panda Timestamp object
        data.time_over = pd.to_datetime(data['time_over'], dayfirst="True")

        # Set as dataframe index the waypoint order
        data  = data.set_index('order')

        # Delete columns that are empty and do not provide any value
        data = data.drop(["trajectory_id",
                          "distance",
                          "visible",
                          "id",
                          "rel_dist",
                          "coords"], axis=1)

        # Change name of Dataframe columns
        data.rename(columns = {
                       data.columns[3]: "ac_type",
                       data.columns[4]: "wpt_type",
                       data.columns[5]: "x_coord",
                       data.columns[6]: "y_coord"},
                    inplace=True)

        # Only get cruise waypoints
        if cruise:
            data = data.loc[data.fl > 150.]
            data = data.reset_index()
            data = data.drop('order',axis=1)

        return data

    @staticmethod
    def _avg_spd(wpt1,wpt2):
        """
        Function calculates the average speed between two way-points, using the distance travelled and time, and
        using flat earth approximation.
        :param wpt1: dataframe of current way-point
        :param wpt2: dataframe of way-point to reach
        :return: speed (kts) and heading to fly from way-point 1 to waypoint 2
        """
        # obtain average speed between 2 waypoints and the heading the aircraft must fly to reach next waypoint
        hdg, dist = geo.qdrdist(wpt1['x_coord'],
                                wpt1['y_coord'],
                                wpt2['x_coord'],
                                wpt2['y_coord'])

        time_lapse_second = pd.to_timedelta(wpt2.time_over - wpt1.time_over, unit='s').total_seconds() # in seconds
        time_lapse = np.divide(time_lapse_second, 3600) # convert to hr because kts is nm/h

        v_tas = aero.kts * np.divide(dist, time_lapse) # in kts

        h = aero.ft * np.mean(np.array([int("".join([str(wpt1.fl),"00"])),
                                        int("".join([str(wpt2.fl), "00"]))]))

        v_cas = aero.tas2cas(v_tas,h) / aero.kts

        return v_cas,hdg

    def _cre(self):
        """
        Include BlueSky CRE stack command, that creates the aircraft
        :return: string of CRE stack command
        """
        # TODO add code to accommodate option to start the simulation at the origin and end at destination

        spd,hdg = self._avg_spd(self.data.iloc[0],self.data.iloc[1])
        spd = str(int(spd))

        return '00:00:00.00>CRE ' + ", ".join([self.acid, self.ac_type,
                                             str(self.data.iloc[0].x_coord),
                                             str(self.data.iloc[0].y_coord),
                                             str(hdg),
                                             str(self.data.iloc[0].fl) + "00",
                                             spd]) + "\n"

    def start_simulation(self):
        """
        Include VNAV,LNAV,op,ff stack commands. These are the commands that start the simulation in BlueSky.
        In addition here is where you create a log file

        :return: string of VNAV,LNAV,op,ff stack commands
        """

        return "0:00:00.00>lnav {} ON \n0:00:00.00>vnav {} ON \n00:00:00.00>op \n00:00:00.05>ff\n".\
            format(self.acid, self.acid)

    def start_log(self,log_type,period=1.0,variables='id,lat,lon,alt,gs,cas,traf.perf.mass,traf.'):
        """

        :param log_type: select way in which to log information and give appropriate stack command
        :param period: if log_type is periodic, the select period between logging information
        :param varaibles: string of variables to log data
        :return:
        """
        if  log_type == 'periodic':

            return  "0:00:00.00>crelog STANDARD {} \n".format(period) + \
                    "0:00:00.00>STANDARD ADD {}\n".format(variables) + \
                    "0:00:00.00>STANDARD ON\n"

        elif log_type == 'waypoint':

            return  "0:00:00.00>WPTLOG ON\n"

    def get_route(self):

        return "0:00:00.00>DUMPRTE {}\n".format(self.acid)

    def initialise_simulation(self):
        """
        Include HOLD, DATE stack command.
        :return: string of HOLD, DATE stack commands
        """
        return "00:00:00.00>hold \n00:00:00.00>date {}\n".format(self.date_start.strftime("%d %m %Y %H:%M:%S.00")) + \
               self._cre()


    def defwpt_command(self):
        """
        Defines the way-points in the trajectory data as way-points in BlueSky that the FMS can use for LNAV.
        :return:
        """

        all_defwpt = []

        for idx in range(1, self.data.index.size):

            defwpt = '0:00:00.00>defwpt ' + 'wpt_{}'.format(idx) + ' ' + \
                     str(self.data.iloc[idx].x_coord) + ' ' + \
                     str(self.data.iloc[idx].y_coord) + ' ' + \
                     '\n'
            all_defwpt.append(defwpt)

        return "".join(all_defwpt)

    def addwpt_command(self,with_spd=True):
        """
        Defines the sequence of way-points, for the BlueSKy FMS, that the aircraft must follow.
        :return:
        """

        all_after = []

        for idx in range(1, self.data.index.size):

            if with_spd:
                spd, hdg = self._avg_spd(self.data.iloc[idx-1], self.data.iloc[idx])

                wpt = '0:00:00.00>addwpt ' + ",".join(['{},wpt_{}'.format(self.acid,idx),
                                                       'FL{}'.format(str(self.data.iloc[idx].fl)),
                                                       '{}'.format( str(int(spd))) + "\n"])
            else:
                wpt = '0:00:00.00>addwpt ' + ",".join(['{},wpt_{}'.format(self.acid,idx),
                                                       'FL{}'.format(str(self.data.iloc[idx].fl) + "\n")])
            all_after.append(wpt)

        return "".join(all_after)

    def rta_command(self,wptList):
        """
        :param wpt:
        :return:
        """
        rtas = []

        for wpt in wptList:

            time = self.data.loc[wpt].time_over.time().strftime("%H:%M:%S")
            rtaCmd =  "0:00:00.00>{} ".format(self.acid) + "RTA_AT " + "wpt_{} ".format(str(wpt)) + \
                        time + "\n"
            rtas.append(rtaCmd)

        return "".join(rtas)

    def twSize_command(self,wptList,twSize):
        """
        :param wpt:
        :return:
        """
        rtas = []

        for wpt in wptList:

            rtaCmd =  "0:00:00.00>{} ".format(self.acid) + "TW_SIZE_AT " + "wpt_{} ".format(str(wpt)) + \
                        str(twSize) + "\n"
            rtas.append(rtaCmd)

        return "".join(rtas)

    def afms_command(self,wptList,twType):

        rtas = []

        for wpt in wptList:

            rtaCmd =  "0:00:00.00>{} ".format(self.acid) + "AFMS_FROM " + "wpt_{} ".format(str(wpt)) + twType + "\n"
            rtas.append(rtaCmd)

        return "".join(rtas)
