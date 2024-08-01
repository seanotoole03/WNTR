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
from collections import OrderedDict

import argparse
from pyModbusTCP.server import ModbusServer, DataHandler
from pyModbusTCP.constants import EXP_ILLEGAL_FUNCTION
from pyModbusTCP.client import ModbusClient

import random as rand

import pycomm3
import serial

import os
#print(os.environ.get('VIRTUAL_ENV'))
# Create a water network model
inp_file = 'examples/networks/Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
wn2 = wntr.network.WaterNetworkModel(inp_file)
wn_baseline = wntr.network.WaterNetworkModel(inp_file)
i = 0
for control_name, control in wn._controls.items():
            #print(control_name + " : " + control.__str__())
            #print(control.__str__())
            control_assign = wn.get_control(control_name)
            if(i<=13):
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

## WN2 control and PLC assignments
i = 0
for control_name, control in wn2._controls.items():
            #print(control_name + " : " + control.__str__())
            #print(control.__str__())
            control_assign = wn2.get_control(control_name)
            if(i<=13):
                control_assign.assign_cps("PLC1") #does not create an actual CPS node by the name of SCADA1, simply creates a label which can be used as reference against the CPS control node registry
            else:
                control_assign.assign_cps("PLC2")
            i+=1
            
wn2._cps_reg.add_PLC("PLC1")
wn2._cps_reg.add_PLC("PLC2")
wn2._cps_reg.add_SCADA("SCADA1")
wn2._cps_reg["SCADA1"].add_owned("PLC1")
wn2._cps_reg["SCADA1"].add_owned("PLC2")
wn2._cps_reg.add_RTU("RTU1")
wn2._cps_reg.add_RTU("RTU2")

wn2._cps_edges.add_MODBUS("s1_MOD_p1","SCADA1","PLC1")
wn2._cps_edges.add_MODBUS("s1_MOD_p2","SCADA1","PLC2")


############ Simulate hydraulics (EPANET) ############

wn.options.time.hydraulic_timestep = 3600
wn.options.time.duration = 48 * 3600 #new time of 30hr to allow for tank manipulation effect to propogate across time
sim1 = wntr.sim.WNTRSimulator(wn)
res1 = sim1.run_sim()

############ Simulate hydraulics (epanet stepped) ############

# 24 hour simulation done in 1 x 12-hour chunk, 12 x 1-hour chunks

#simulate first 12 hours
wn2.options.time.duration = 12 * 3600
sim2 = wntr.sim.WNTRSimulator(wn2)
res2 = sim2.run_sim()
wn2.options.time.pattern_start = wn2.options.time.pattern_start + (12 * 3600)
print(res2.node['head'])
############ Spin up communication client & servers ############

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
print("SCADA connection to PLC1: {open}".format(open = c.open()))
c.close()
#spin up modbus client for attacker
c2 = ModbusClient(host='localhost', port=502, auto_open=True, debug=False)
print("Attacker connection to PLC1: {open}".format(open = c2.open()))
c.close()
#internal to server 1, set holding registers
##Note: registers hold only 16bits, capping values storable at 65535. Thus, we should be careful to avoid
## writing any values which could overflow. Most sensors seem to use 2 significant digits after the decimal,
## so to preserve those in the int16 registers we should usually elevate values to be written by 1e2
## values pulled from servers should then be scaled by 1e-2 to get accurate values for client controller to
## use in control decisions.
## Alternatively, we can use a multi-register scheme to register values up to 32 bits, so long as we know both
## which registers will be high and low and what the direction (endianness) of the 

#print(res2.node["head"].iloc[12,:])
server.data_bank.set_holding_registers(0x0000,(res2.node["head"].iloc[12,:])*1e3)
print("Check MODBUS holding registers following 12hr runtime and regset: ")
c.open()
print(numpy.array(c.read_holding_registers(0x0000,97), dtype=numpy.float32)*1e-3)
#np.array([1.0000123456789, 2.0000123456789, 3.0000123456789], dtype=np.float64)
res_groundTruth = res2.deep_copy()
ctl_store = OrderedDict()
c.close()
#simulate 36 hours in 36 1-hour chunks
for i in range(36):
    curr_t = 12+i+1
    wn2.options.time.duration = 1 * 3600
    res3 = sim2.run_sim(prev_results=res_groundTruth)
    #res3._adjust_time(12+i*3600)
    res_groundTruth.append(res3, overwrite=False) #keep unmodified values 
    #print(res3.node["head"])
    server.data_bank.set_holding_registers(0x0000,(res3.node["head"].iloc[curr_t,:])*1e3) #store head values
    server.data_bank.set_holding_registers(0x0061,(res3.node["pressure"].iloc[curr_t,:])*1e3) #store pressure values
    c2.open()
    #print("Pulled MODBUS holding registers following {time} hr runtime and regset: {open} ".format(time = curr_t, open = c2.is_open))

    if i >= 7: #at 18hr into simulation, overwrite head values for tank1 to cause tank to continue to drain
        h = numpy.array(c2.read_holding_registers(0x0000,97), dtype=numpy.float32)*1e-3 #read head values
        p = numpy.array(c2.read_holding_registers(0x0061,97), dtype=numpy.float32)*1e-3 #read pressure values
        if (h[92]-39.96) < 5.21: #head(meters)-initial elevation; 5.21m = 17.1ft; 45.17m ~> 17.1ft relative head
            r = rand.gauss(0.1,0.03)
            nv = 45.17+r
            pv = 7.6+r
            if c2.write_single_register(0x005E,int(nv*1e3)): #overwrite t1 head at reg 94 (hex 5E) with incorrect head which would read as above switching level
                res3.node["head"].loc[(12+i+1)*3600,'1'] = nv #conditionally set backend values
                print("Head value tank 1 overwritten, showing open-valve levels")
            if c2.write_multiple_registers(0x0061,[int(pv*1e3)]): #overwrite t1 head with incorrect head which would read as safe
                res3.node["pressure"].loc[(12+i+1)*3600,'1'] = pv #conditionally set backend values
                print("Pressure value tank 1 overwritten, showing open-valve levels")
                if wn2._controls.get("control 15") != None:
                    ctl_store["control 15"] = wn2.get_control("control 15")
                    wn2._cps_reg["PLC2"].disable_control("control 15")
                    print("Control 15 deleted.")
                # removed control: "IF TANK 1 LEVEL BELOW 5.21208 THEN PUMP 335 STATUS IS OPEN PRIORITY 3"
                if wn2._controls.get("control 17") != None:
                    ctl_store["control 17"] = wn2.get_control("control 17")
                    wn2._cps_reg["PLC2"].disable_control("control 17")
                    print("Control 17 deleted.")
                # removed control: "IF TANK 1 LEVEL BELOW 5.21208 THEN PIPE 330 STATUS IS CLOSED PRIORITY 3"
                #wn.set_initial_conditions(res3) #only applies to controller perception, not ground truth
        else: 
            if len(ctl_store) != 0: #re-add controls for timesteps where attack does not take effect
                for control_name, control in ctl_store.items():
                    wn2.add_control(control_name, control)
                    print("Control {name} re-added.".format(name=control_name))
                ctl_store.clear()
                
    c2.close()
    c.open()
    print("SCADA client can still connect: {open} ".format(open = c.is_open))    
    c.close()
    #print(numpy.asarray(c.read_holding_registers(0x0000,97))*1e-2)
    #print(res3.node["head"].iloc[12+i+1,:]*1e3)
    res2.append(res3)  #append tampered values
    wn2.options.time.pattern_start = wn2.options.time.pattern_start + (1 * 3600)
    wn2.set_initial_conditions(res_groundTruth)
    sim2 = wntr.sim.WNTRSimulator(wn2)

#print(res1.link)
#print(res2.link)
#print("Final holding register states (node head):")
#c.open()
#print(numpy.array(c.read_holding_registers(0x0000,97), dtype=numpy.float32)*1e-3)
#c.close()
res4 = abs(res1 - res2).max()
#print(res4.link)

node_keys = ["demand", "head", "pressure"]
for key in node_keys:
    max_res_diff_node = res4.node[key].max()

link_keys = ["flowrate", "velocity", "status", "setting"]
for key in link_keys:
    max_res_diff_link = res4.link[key].max()

print("Verify node values for WNTR simulator multi-step runtime (1x12h block + 12x1h blocks) with MODBUS against WNTR simulator in one 24h block. Max diff between output arrays: " + str(max_res_diff_node))
print("Verify link values for WNTR simulator multi-step runtime (1x12h block + 12x1h blocks) with MODBUS against WNTR simulator in one 24h block. Max diff between output arrays: " + str(max_res_diff_link))

wn_baseline.options.time.hydraulic_timestep = 3600
wn_baseline.options.time.duration = 48 * 3600
simbase = wntr.sim.WNTRSimulator(wn_baseline)
resbase = simbase.run_sim()

#plotting experiment
pressure1 = res2.node['head'].loc[:,wn.node_name_list]
print(pressure1)
groundtruth = res_groundTruth.node['head'].loc[:,wn.node_name_list]
print(groundtruth)
pressurebase = resbase.node['head'].loc[:, wn_baseline.node_name_list]
#tankH = tankH * 3.28084 # Convert tank head to ft
pressure1.index /= 3600 # convert time to hours
fig = px.line(pressure1)
fig = fig.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
fig.write_html('CPS_Net3_Attack_MODBUS_T1_head_falseFeedback.html')

groundtruth.index /= 3600 # convert time to hours
figg = px.line(groundtruth)
figg = figg.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
figg.write_html('CPS_Net3_Attack_MODBUS_T1_head_groundTruth.html')

pressurebase.index /= 3600 # convert time to hours
figb = px.line(pressurebase)
figb = figb.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
figb.write_html('CPS_Net3_Baseline_head.html')