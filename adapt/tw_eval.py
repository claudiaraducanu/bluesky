import numpy as np
import os, datetime
import pandas as pd
import copy
from datetime import time
import matplotlib.pyplot as plt
from netCDF4 import num2date











# def convert_sec2dhms(sec):
#
#     day = sec // (24 * 3600)
#     time = sec % (24 * 3600)
#     hour = time // 3600
#     time %= 3600
#     minutes = time // 60
#     time %= 60
#     seconds = time
#
#     return  day,hour,minutes,seconds
#
# results_path = "results_wind_analysis/rta/wpt_4"
# col = []
#
# for file in os.listdir(results_path):
#     # col.append("_".join(os.path.splitext(file)[0].split("_")[2:-2]))
#     col.append(os.path.splitext(file)[0].split("_")[1])
#
# fuel_consumption = pd.DataFrame(columns=col)
# flight_time      = pd.DataFrame(columns=col)
#
# for idx,file in enumerate(os.listdir(results_path)):
#
#     data = pd.read_csv(os.path.join(results_path, file), sep=",")
#     fuel_consumption[col[idx]] = data.fuel_mass.values
#     flight_time[col[idx]] = data.simt.values
#
#
# ######################################################
# """Convert the flight time to hh:mm:ss""" #05:44:11
# ######################################################
# time_values = num2date(flight_time.iloc[14].values,units="seconds since 2014-09-09 05:12:46",
#                calendar='gregorian')
# total_time = pd.DataFrame(time_values, columns=['sim_arrival_time'],index=flight_time.iloc[14].index)
# total_time['rta_from_ddr'] = datetime.datetime(year=2014,month=9,day=9,hour=5,minute=44,second=11)
# total_time['sim_arrival_time - rta_from_ddr'] = pd.concat([total_time['rta_from_ddr'],total_time['sim_arrival_time']], axis=1).max(axis=1)-\
# pd.concat([total_time['rta_from_ddr'], total_time['sim_arrival_time']], axis=1).min(axis=1)
# total_time.to_excel("ADH931_wind_wpt4_rta_total_time.xlsx", sheet_name='Sheet1',
#                    na_rep='', float_format=None, columns=None,
#                    header=True, index=True, index_label=None,
#                    startrow=0, startcol=0, engine=None, merge_cells=True,
#                    encoding=None, inf_rep='inf', verbose=True, freeze_panes=None)
#
# ######################################################
# """Fuel consumed [kg"""
# ######################################################
#
# total_fuel = fuel_consumption.iloc[14].values
# total_fuel = pd.DataFrame(total_fuel, columns=['fuel'],index=flight_time.iloc[14].index).T
# total_fuel.to_excel("ADH931_wind_wpt4_rta_total_fuel.xlsx", sheet_name='Sheet1',
#                    na_rep='', float_format=None, columns=None,
#                    header=True, index=True, index_label=None,
#                    startrow=0, startcol=0, engine=None, merge_cells=True,
#                    encoding=None, inf_rep='inf', verbose=True, freeze_panes=None)
# ######################################################
# """ Regular plots """
# ######################################################

# ylabel_c = np.arange(round(fuel_consumption.min().min()),round(fuel_consumption.max().max())+100,100)
# # print(flight_time)
# f3, ax3 = plt.subplots(1,1)
# for c in flight_time.columns:
#     ax3.scatter(np.array(fuel_consumption.index),fuel_consumption[c],marker = 'x',label=c)
# plt.xlabel("Waypoint")
# plt.ylabel("Fuel [kg]")
# plt.yticks(ylabel_c)
# plt.legend()
# plt.title("Fuel consumption ADH931")
# ax3.yaxis.grid()
# plt.savefig("ADH931_wind_fuel_consumption.png", dpi=None, facecolor='w', edgecolor='w',
#         orientation='portrait', papertype=None, format=None,
#         transparent=False, bbox_inches=None, pad_inches=0.1,
#         frameon=None, metadata=None)
# plt.show()
#
#
# ylabel_t = np.arange(round(flight_time.min().min()),round(flight_time.max().max())+1,250)
# # print(flight_time)
# f2, ax2 = plt.subplots(1,1)
# for c in flight_time.columns:
#     ax2.scatter(np.array(flight_time.index),flight_time[c],marker = 'x',label=c)
# plt.xlabel("Waypoint")
# plt.ylabel("Time [s]")
# plt.yticks(ylabel_t)
# plt.legend()
# plt.title("Flight Time ADH931")
# ax2.yaxis.grid()
# plt.savefig("ADH931_wind_flight_time.png", dpi=None, facecolor='w', edgecolor='w',
#         orientation='portrait', papertype=None, format=None,
#         transparent=False, bbox_inches=None, pad_inches=0.1,
#         frameon=None, metadata=None)
# plt.show()

# ######################################################
# """ Percentage Change from the average speed plots """
# ######################################################
#
# pc_column = "df0"
# reference_fuel = copy.deepcopy(fuel_consumption[pc_column])
# reference_time = copy.deepcopy(flight_time[pc_column])
#
# for c in col:
#     fuel_consumption[c] = (fuel_consumption[c] - reference_fuel )/reference_fuel * 100
#     flight_time[c] = (flight_time[c]-reference_time) / reference_time * 100
#     # print(flight_time)
#
# ft = flight_time
# fc = fuel_consumption
#
# ylabel_c = np.arange(round(fc.min().min()),round(fc.max().max())+1,0.25)
# ylabel_t = np.arange(round(ft.min().min()),round(ft.max().max())+1,0.5)
#
# # Plots
# f, ax = plt.subplots(1,1)
# for c in fc.columns:
#     ax.scatter(fc.index,fc[c],marker='x',label=c)
#
# plt.xlabel("Waypoint")
# plt.ylabel("Percentage change \nfrom {}".format(pc_column))
# plt.yticks(ylabel_c)
# plt.legend()
# plt.title("Fuel Consumption ADH931")
# ax.yaxis.grid()
# plt.savefig("ADH931_wind_fuel_consumption_{}.png".format(pc_column), dpi=None, facecolor='w', edgecolor='w',
#         orientation='portrait', papertype=None, format=None,
#         transparent=False, bbox_inches=None, pad_inches=0.1,
#         frameon=None, metadata=None)
# plt.show()
#
#
# # print(flight_time)
# f1, ax1 = plt.subplots(1,1)
# for c in ft.columns:
#     ax1.scatter(ft.index,ft[c],marker='x',label=c)
# plt.xlabel("Waypoint")
# plt.ylabel("Percentage change \nfrom {}".format(pc_column))
# plt.yticks(ylabel_t)
# plt.legend()
# plt.title("Flight Time ADH931")
# ax1.yaxis.grid()
# plt.savefig("ADH931_wind_flight_time_{}.png".format(pc_column), dpi=None, facecolor='w', edgecolor='w',
#         orientation='portrait', papertype=None, format=None,
#         transparent=False, bbox_inches=None, pad_inches=0.1,
#         frameon=None, metadata=None)
# plt.show()
#
# plt.close()