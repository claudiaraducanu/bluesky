import os,datetime
import pandas as pd


def convert_sec2dhms(sec):

    day = sec // (24 * 3600)
    time = sec % (24 * 3600)
    hour = time // 3600
    time %= 3600
    minutes = time // 60
    time %= 60
    seconds = time

    return  day,hour,minutes,seconds

def ensemble_mean(path):

    kts = 0.514444              # m/s  of 1 knot
    col=["simt","acid","ens","lat","lon","alt",'tas',"cas","gs","mass"] # logged data

    # dataframe of results from simulation in which average speed between two waypoints is used.

    log_lines = pd.DataFrame(columns=col)

    for file in os.listdir(path):

        data = pd.read_csv(os.path.join(path,file), sep = ",", header=None,
                       names= ["simt","acid","ens","lat","lon","alt",'tas',"cas","gs","mass"],
                        skiprows=8)
        log_lines = pd.concat([log_lines, data])

    first_wpt = log_lines.index.min()
    last_wpt = log_lines.index.max()

    log_lines.index.names = ['wpt']

    # Set index the (wpt,ensemble) as dataframe index
    log_lines = log_lines.set_index([log_lines.index, 'ens'])
    log_lines = log_lines.sort_index()

    # Average
    print('Results from directory: {dir}'.format(dir=path))
    print("Flight time %02f" % log_lines.loc[last_wpt, :].mean().simt)
    print("Flight time %d %d:%02d:%02d" % (convert_sec2dhms(log_lines.loc[last_wpt, :].mean().simt)))
    print('Fuel Consumption {fc}'.format(fc=log_lines.loc[first_wpt, :].mean().mass -
                                            log_lines.loc[last_wpt, :].mean().mass))

    log_lines[['cas', 'gs', 'tas']] = log_lines[['cas', 'gs', 'tas']] / kts
    log_lines = log_lines.groupby('wpt').mean()
    log_lines = log_lines.reset_index(level='wpt')

    return log_lines

