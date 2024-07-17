"""
The following test shows a full implementation of basic CPS_Node features of the WNTR+CPS module on the Net3 network file.
"""
import wntr
from wntr.network.CPS_node import SCADA, PLC, RTU, MODBUS, EIP, SER, CPSNodeRegistry, CPSEdgeRegistry
import wntr.network.io
import wntr.metrics.topographic
from wntr.network.layer import autogenerate_full_cps_layer
import plotly.express as px
import networkx as nx
import numpy
import pandas as pd
import argparse
from pyModbusTCP.server import ModbusServer, DataHandler
from pyModbusTCP.constants import EXP_ILLEGAL_FUNCTION
from pyModbusTCP.client import ModbusClient

import pycomm3
import serial

import os
#print(os.environ.get('VIRTUAL_ENV'))
# Create a water network model
inp_file = '../networks/wadi_topology/wadi_map.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
autogenerate_full_cps_layer(wn, placement_type='complex', timed_control_assignments='local', edge_types='MODBUS', verbose=0)
wn.options.time.duration = 86400
# Need EPANET sim for water quality analysis
sim = wntr.sim.WNTRSimulator(wn)
results = sim.run_sim()  
#df_node = pd.DataFrame([])
for key in results.node:
    #print(results.node[key].to_csv("wadi_out.csv",mode='a'))
    print(key)
    print(results.node[key].loc[86400,:].to_csv())
    #pd.concat([df,results.node[key]],sort='false')
#df_link = 
for key in results.link:
    print(key)
    #print(results.link[key].to_csv("wadi_out.csv",mode='a'))
    print(results.link[key].loc[86400,:].to_csv())
    #pd.concat([df,results.link[key]],sort='false')    
#df.to_csv("wadi_out.csv")
#print(df)