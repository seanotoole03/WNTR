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

# Create a water network model
inp_file = '../networks/Net3.inp'
wn_controller = wntr.network.WaterNetworkModel(inp_file)
#wn_baseline = wntr.network.WaterNetworkModel(inp_file)
i = 0
for control_name, control in wn_controller._controls.items():
            print(control_name + " : " + control.__str__())
            #print(control.__str__())
            control_assign = wn_controller.get_control(control_name)
            if(i<13):
                control_assign.assign_cps("PLC1") #does not create an actual CPS node by the name of SCADA1, simply creates a label which can be used as reference against the CPS control node registry
            else:
                control_assign.assign_cps("PLC2")
            i+=1
            
wn_controller._cps_reg.add_PLC("PLC1")
wn_controller._cps_reg.add_PLC("PLC2")
wn_controller._cps_reg.add_SCADA("SCADA1")
wn_controller._cps_reg["SCADA1"].add_owned("PLC1")
wn_controller._cps_reg["SCADA1"].add_owned("PLC2")
wn_controller._cps_reg.add_RTU("RTU1")
wn_controller._cps_reg.add_RTU("RTU2")

wn_controller._cps_edges.add_MODBUS("s1_MOD_p1","SCADA1","PLC1")
wn_controller._cps_edges.add_MODBUS("s1_MOD_p2","SCADA1","PLC2")
#wn_controller._cps_edges.add_EIP("s1_EIP_p1","SCADA1","PLC1")
#wn_controller._cps_edges.add_EIP("s1_EIP_p2","SCADA1","PLC2")
#wn_controller._cps_edges.add_SER("s1_SER_p1","SCADA1","PLC1")
#wn_controller._cps_edges.add_SER("s1_SER_p2","SCADA1","PLC2")
wn_controller._cps_edges.add_SER("r1_SER_p1","RTU1","PLC1")
wn_controller._cps_edges.add_SER("r2_SER_p2","RTU2","PLC2")

#plc-to-plc edge added for duplication/connectivity
wn_controller._cps_edges.add_MODBUS("p1_MOD_p2","PLC1","PLC2")
wn_controller._cps_edges.add_SER("r1_SER_p2","RTU1","PLC2")
wn_controller._cps_edges.add_SER("r2_SER_p1","RTU2","PLC1")


############ Simulate hydraulics ############

wn_controller.options.time.hydraulic_timestep = 3600
wn_controller.options.time.duration = 24 * 3600
sim1 = wntr.sim.EpanetSimulator(wn_controller)
res1 = sim1.run_sim()

# 24 hour simulation done in 2 12-hour chunks
# initial run (first timestep, set up the results object) 
# spin up modbus server for PLC1
# parse args
parser = argparse.ArgumentParser()
parser.add_argument('-H', '--host', type=str, default='localhost', help='Host (default: localhost)')
parser.add_argument('-p', '--port', type=int, default=502, help='TCP port (default: 502)')
args = parser.parse_args()
# init modbus server and start it
server = ModbusServer(host='127.0.0.1', port=args.port, no_block=True)
server.start()
server2 = ModbusServer(host='127.0.0.2', port=503, no_block=True)
server2.start()

#spin up modbus client for SCADA
c = ModbusClient(host='localhost', port=502, auto_open=True, debug=False)

#simulate first 12 hours
wn_controller.options.time.duration = 12 * 3600
sim2 = wntr.sim.EpanetSimulator(wn_controller)
res2 = sim2.run_sim()

#send communication requesting coil info
coils_l = c.read_coils(0, 10)
c.port = 503
c.host = '127.0.0.2'
if c.open():
    is_ok = c.write_single_coil(0, True)
    if is_ok:
        print('coil #%s: write to %s' % (0, True))
    else:
        print('coil #%s: unable to write %s' % (0, True))
coils_l2 = c.read_coils(0, 10)
print(c.read_holding_registers(0x0000,10))
c.port = 502
c.host = 'localhost'
print(c.open())
# if success display registers
if coils_l:
    print('coil ad #0 to 9: %s' % coils_l)
else:
    print('unable to read coils')
if coils_l2:
    print('coil ad #0 to 9: %s' % coils_l2)
else:
    print('unable to read coils')
    
    
#internal to server 1, set holding registers
##Note: registers hold only 16bits, capping values storable at 65535. Thus, we should be careful to avoid
## writing any values which could overflow. Most sensors seem to use 2 significant digits after the decimal,
## so to preserve those in the int16 registers we should usually elevate values to be written by 1e2
## values pulled from servers should then be scaled by 1e-2 to get accurate values for client controller to
## use in control decisions.

print(res2.node["pressure"].iloc[12,:])
server.data_bank.set_holding_registers(0x0000,(res2.node["pressure"].iloc[12,:])*1e2)
print(numpy.asarray(c.read_holding_registers(0x0000,97))*1e-2)

#simulate second 2 hours
wn_controller.set_initial_conditions(res2)
wn_controller.options.time.pattern_start = wn_controller.options.time.pattern_start + ((12) * 3600)
wn_controller.options.time.duration = 12 * 3600
sim2 = wntr.sim.EpanetSimulator(wn_controller)
res3 = sim2.run_sim()
res3._adjust_time((12)*3600)
res2.append(res3)  
res4 = abs(res1 - res2).max()

node_keys = ["demand", "head", "pressure"]
for key in node_keys:
    max_res_diff_node = res4.node[key].max()

link_keys = ["flowrate", "velocity", "status", "setting", "headloss"]
for key in link_keys:
    max_res_diff_link = res4.link[key].max()

print(max_res_diff_node)
print(max_res_diff_link)

