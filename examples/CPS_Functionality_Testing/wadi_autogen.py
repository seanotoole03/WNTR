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
autogenerate_full_cps_layer(wn, placement_type='complex', timed_control_assignments='local', edge_types='MODBUS', verbose=1)