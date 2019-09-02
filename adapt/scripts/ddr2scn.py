"""
This module converts the DDR2 files to Bluesky scenario file format.

Created by: Claudia Raducanu
Date: 5.03.2019
"""
import os
import pandas as pd
import sys
sys.path.append('/Users/Claudia/Documents/5-MSc-2/bluesky')
from    bluesky.tools import aero, geo
import  numpy as np
import  datetime

class parseDDR():


    def __init__(self,fpath,cruise=True):
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
        self.tw_probabilistic = None
        self.tw_deterministic = None

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
        # BADA cruise refernce mach used after FL140 => FL140 change cruise way-point threshold
        if cruise:
            data = data.loc[data.fl > 140.]
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

    def cre(self,cascr):
        """
        Include BlueSky CRE stack command, that creates the aircraft
        :return: string of CRE stack command
        """

        _,hdg = self._avg_spd(self.data.iloc[0],self.data.iloc[1])

        return '00:00:00.00>CRE ' + ", ".join([self.acid, self.ac_type,
                                               str(self.data.iloc[0].x_coord),
                                               str(self.data.iloc[0].y_coord),
                                               str(hdg),
                                               str(self.data.iloc[0].fl) + "00",
                                               str(cascr) + "\n"])

    def start_simulation(self):
        """
        Include VNAV,LNAV,op,ff stack commands. These are the commands that start the simulation in BlueSky.
        In addition here is where you create a log file

        :return: string of VNAV,LNAV,op,ff stack commands
        """

        return "0:00:00.00>lnav {} ON \n" \
               "0:00:00.00>vnav {} ON \n" \
               "00:00:00.00>op \n" \
               "00:00:01.00>ff\n".format(self.acid, self.acid)


    def initialise_simulation(self,delay):

        """
        Include HOLD, DATE stack command.
        :return: string of HOLD, DATE stack commands
        """

        departure_time = self.date_start + datetime.timedelta(minutes = delay)

        return "00:00:00.00>hold \n" \
               "00:00:00.00>date {}\n".format(departure_time.strftime("%d %m %Y %H:%M:%S.00"))


    def defwpt_command(self):
        """
        Defines the way-points in the trajectory data as way-points in BlueSky that the FMS can use for LNAV.
        :return:
        """

        all_defwpt = []

        for idx in range(0, self.data.index.size):

            defwpt = '0:00:00.00>defwpt ' + 'wpt_{}'.format(idx) + ' ' + \
                     str(self.data.iloc[idx].x_coord) + ' ' + \
                     str(self.data.iloc[idx].y_coord) + ' ' + \
                     '\n'
            all_defwpt.append(defwpt)

        return "".join(all_defwpt)

    def addwpt_command(self):
        """
        Defines the sequence of way-points, for the BlueSKy FMS, that the aircraft must follow.
        :return:
        """

        all_after = []

        for idx in range(0, self.data.index.size):

            wpt = '0:00:00.00>addwpt ' + ",".join(['{},wpt_{}'.format(self.acid,idx),
                                                       'FL{}'.format(str(self.data.iloc[idx].fl) + "\n")])
            all_after.append(wpt)

        return "".join(all_after)

    def rta_commands(self,tw_type,wp_freq,delay):

        if tw_type == "60" or  tw_type == "15":

            rtaWpts = [self.data.index[-1]]

        else:

            # define the way-points that have an RTA constraint. Start out with the first way-point
            # such that the AFMS is activated and then continue such that there is a waypoint
            # with an RTA at least wp_frequency seconds (set in adaptsettings.cfg) away from the last
            # waypoint with an RTA.

            rtaWpts = []  # list of way-points that have an RTA constraint

            current_wp   = 0                    # start from first way-point
            current_time = self.date_start

            # as long as there are way-points
            while current_wp < self.data.index[-1]:

                # calculate the number of seconds from current way-point to all the other way-points left in
                # the trajectory
                wp_timedelta = (self.data['time_over'][current_wp + 1:] - current_time).dt.total_seconds()
                wp_timedelta = wp_timedelta[wp_timedelta > int(wp_freq)]

                if not wp_timedelta.size:
                    current_wp   = self.data.index[-1]
                else:
                    current_wp = wp_timedelta.index[0]
                    current_time = self.data['time_over'][current_wp]
                    rtaWpts.append(current_wp)

        rtaTimes                = self.data['time_over'].iloc[rtaWpts]
        departureTime           = self.date_start + datetime.timedelta(minutes = delay)
        wp_afterdeparturetime   = (rtaTimes - departureTime).dt.total_seconds() > 0
        rtaWpts                 = list(rtaTimes[wp_afterdeparturetime].index)

        cmdrtas     = []

        for wpt in rtaWpts:

            # set the required arrival time at a way-point to be DDR time over
            rtatime = self.data.loc[wpt].time_over.strftime("%d %m %Y %H:%M:%S.00")

            # RTA_AT
            cmdrta =  "0:00:00.00>RTA {} ".format(self.acid) + "wpt_{} ".format(str(wpt)) + \
                      rtatime  + "\n"
            cmdrtas.append(cmdrta)

        return "".join(cmdrtas)

