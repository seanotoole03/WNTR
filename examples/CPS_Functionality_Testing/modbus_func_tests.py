"""
The following test shows a full implementation of basic CPS_Node features of the WNTR+CPS module on the Net3 network file.
"""
import wntr
from wntr.network.CPS_node import SCADA, PLC, RTU, MODBUS, EIP, SER, CPSNodeRegistry, CPSEdgeRegistry
import wntr.network.io
import wntr.metrics.topographic
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
inp_file = '../networks/Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
i = 0
for control_name, control in wn._controls.items():
            #print(control_name + " : " + control.__str__())
            #print(control.__str__())
            control_assign = wn.get_control(control_name)
            if(i<13):
                control_assign.assign_cps("PLC1") #does not create an actual CPS node by the name of SCADA1, simply creates a label which can be used as reference against the CPS control node registry
            else:
                control_assign.assign_cps("PLC2")
            i+=1
            
wn._cps_reg.add_PLC("PLC1")
wn._cps_reg.add_PLC("PLC2")
wn._cps_reg.add_SCADA("SCADA1")
wn._cps_reg["SCADA1"].add_owned("PLC1")
wn._cps_reg["SCADA1"].add_owned("PLC2")
wn._cps_reg.add_RTU("RTU1")
wn._cps_reg.add_RTU("RTU2")

wn._cps_edges.add_MODBUS("s1_MOD_p1","SCADA1","PLC1")
wn._cps_edges.add_MODBUS("s1_MOD_p2","SCADA1","PLC2")
#wn._cps_edges.add_EIP("s1_EIP_p1","SCADA1","PLC1")
#wn._cps_edges.add_EIP("s1_EIP_p2","SCADA1","PLC2")
#wn._cps_edges.add_SER("s1_SER_p1","SCADA1","PLC1")
#wn._cps_edges.add_SER("s1_SER_p2","SCADA1","PLC2")
wn._cps_edges.add_SER("r1_SER_p1","RTU1","PLC1")
wn._cps_edges.add_SER("r2_SER_p2","RTU2","PLC2")

#plc-to-plc edge added for duplication/connectivity
wn._cps_edges.add_MODBUS("p1_MOD_p2","PLC1","PLC2")
wn._cps_edges.add_SER("r1_SER_p2","RTU1","PLC2")
wn._cps_edges.add_SER("r2_SER_p1","RTU2","PLC1")


############ Simulate hydraulics (EPANET) ############

wn.options.time.hydraulic_timestep = 3600
wn.options.time.duration = 24 * 3600
sim1 = wntr.sim.EpanetSimulator(wn)
res1 = sim1.run_sim()

############ Simulate hydraulics (epanet stepped) ############

# 24 hour simulation done in 1 x 12-hour chunk, 12 x 1-hour chunks

#simulate first 12 hours
wn.options.time.duration = 12 * 3600
sim2 = wntr.sim.EpanetSimulator(wn)
res2 = sim2.run_sim()

############ Spin up communication client & servers ############

##### CURRENT TESTING

server = wn._cps_edges["s1_MOD_p1"]._server
wn._cps_edges["s1_MOD_p1"].connect(start_ip=wn._cps_edges["s1_MOD_p1"]._start_node_ip,start_port=502,end_ip=wn._cps_edges["s1_MOD_p1"]._end_node_ip,end_port=502)
c = wn._cps_edges["s1_MOD_p1"]._c
print(wn._cps_edges["s1_MOD_p1"].to_dict())
server2 = wn._cps_edges["s1_MOD_p2"]._server
wn._cps_edges["s1_MOD_p2"].connect(start_ip=wn._cps_edges["s1_MOD_p2"]._start_node_ip,start_port=503,end_ip=wn._cps_edges["s1_MOD_p2"]._end_node_ip,end_port=502)
print(wn._cps_edges["s1_MOD_p2"]._start_node_ip)
#print(c.read_holding_registers(0x0000,10))
c.port = 502
c.host = 'localhost'
print(c.open())
# if success display registers
# if coils_l:
    # print('coil ad #0 to 9: %s' % coils_l)
# else:
    # print('unable to read coils')
# if coils_l2:
    # print('coil ad #0 to 9: %s' % coils_l2)
# else:
    # print('unable to read coils')
    
    
#internal to server 1, set holding registers
##Note: registers hold only 16bits, capping values storable at 65535. Thus, we should be careful to avoid
## writing any values which could overflow. Most sensors seem to use 2 significant digits after the decimal,
## so to preserve those in the int16 registers we should usually elevate values to be written by 1e2
## values pulled from servers should then be scaled by 1e-2 to get accurate values for client controller to
## use in control decisions.

#print(res2.node["pressure"].iloc[12,:])
server.data_bank.set_holding_registers(0x0000,(res2.node["pressure"].iloc[12,:])*1e2)
print("Check MODBUS holding registers following 12hr runtime and regset: ")
print(numpy.asarray(c.read_holding_registers(0x0000,97))*1e-2)

#simulate second 12 hours in 12 1-hour chunks
for i in range(12):
    curr_t = 12+i+1
    wn.options.time.duration = curr_t * 3600
    res3 = sim2.run_sim()
    #print(res3.node["pressure"])
    server.data_bank.set_holding_registers(0x0000,(res3.node["pressure"].iloc[12+i+1,:])*1e2)
    print("Pulled MODBUS holding registers following {time} hr runtime and regset: {open} ".format(time = curr_t, open = c.is_open))
    #print(numpy.asarray(c.read_holding_registers(0x0000,97))*1e-2)
    res2.append(res3)  
#print(res1.link)
#print(res2.link)
print("Final holding register states (node pressure):")
print(numpy.asarray(c.read_holding_registers(0x0000,97))*1e-2)
res4 = abs(res1 - res2).max()
#print(res4.link)

node_keys = ["demand", "head", "pressure"]
for key in node_keys:
    max_res_diff_node = res4.node[key].max()

link_keys = ["flowrate", "velocity", "status", "setting", "headloss"]
for key in link_keys:
    max_res_diff_link = res4.link[key].max()

print("Verify node values for EPANET simulator multi-step runtime (1x12h block + 12x1h blocks) with MODBUS against EPANET simulator in one 24h block. Max diff between output arrays: " + str(max_res_diff_node))
print("Verify link values for EPANET simulator multi-step runtime (1x12h block + 12x1h blocks) with MODBUS against EPANET simulator in one 24h block. Max diff between output arrays: " + str(max_res_diff_link))

