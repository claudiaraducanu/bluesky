#!/usr/bin/env python
from ecmwfapi import ECMWFDataServer

server = ECMWFDataServer()

server.retrieve({
    "class": "ti",
    "dataset": "tigge",
    "date": "2014-09-08",
    "expver": "prod",
    "grid": "0.5/0.5",
    "levelist": "200/250/300/500/700/850/925/1000",
    "levtype": "pl",
    "number": "1/2/3",
    "origin": "ecmf",
    "param": "131/132",
    "step": "24/30/36",
    "time": "00:00:00",
    "type": "pf",
    "format": "netcdf",
    "target": "tigge_2014-09-08_00_243036.nc"
})