import configparser
import os

def init(cfgfile=''):

    '''Initialize configuration.
       Import config settings from adaptsettings.cfg if this exists, if it doesn't
       create an initial config file'''

    rundir = ''

    if not cfgfile:
        cfgfile = os.path.join(rundir, 'adaptsettings.cfg')

    config = configparser.RawConfigParser()

    if not os.path.isfile(cfgfile):

        print()
        print('No config file adaptsettings.cfg found in the preSim start directory!')
        print()
        print('A default version will be generated,please do not change')
        print()

        # data to be used in adapt simulations
        config.add_section('path')
        config.set('path', 'input_path', os.path.join(rundir, 'input'))
        config.set('path', 'ddr_path',  os.path.join(rundir, 'input/ddr'))
        config.set('path', 'netcdf_path', os.path.join(rundir, 'input/netcdf'))
        config.set('path', 'grib_path', os.path.join(rundir, 'input/grib'))
        config.set('path', 'output_path', 'output')
        config.set('path', 'bluesky_path',  os.path.dirname(os.path.dirname(os.path.dirname( __file__ ))))
        config.set('path', 'scn_path',  os.path.join(os.path.dirname(
            os.path.dirname(os.path.dirname( __file__ ))),'scenario'))

        # Writing our configuration file to 'example.cfg'
        with open(cfgfile, 'w') as configfile:
            config.write(configfile)

    config.read(cfgfile)

    print()
    print("Storing trajectory data in                               ", config[config.sections()[0]]["ddr_path"])
    print("Storing raw wind data ( from ECMWF) in .grb format in    ", config[config.sections()[0]]["grib_path"])
    print("Storing wind data in .nc format in                       ", config[config.sections()[0]]["netcdf_path"])
    print("Storing output of simulations in                         ", config[config.sections()[0]]["output_path"])
    print()

    #TODO create the directories if they do not exit

    return config[config.sections()[0]]









