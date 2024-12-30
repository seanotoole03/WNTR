"""
The following test shows a full implementation of basic CPS_Node features of the WNTR+CPS module on the Net3 network file.
"""
import wntr
from wntr.network.CPS_node import SCADA, PLC, RTU, MODBUS, EIP, SER, CPSNodeRegistry, CPSEdgeRegistry
from wntr.network.base import LinkStatus
from wntr.network.controls import ControlPriority
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

# Create a water network model
inp_file = 'examples/networks/Net3.inp'
wn = wntr.network.WaterNetworkModel(inp_file)
wn2 = wntr.network.WaterNetworkModel(inp_file)
wn_baseline = wntr.network.WaterNetworkModel(inp_file)
wn.options.hydraulic.demand_model = 'PDD'
wn2.options.hydraulic.demand_model = 'PDD'
wn_baseline.options.hydraulic.demand_model = 'PDD'
## Verbosity: 0 for only basic confirmation/error details, 1 for full control list, traffic and step details
verbose = 0

########### WN1 SETUP ###########
## CONTROL ASSIGNMENT: Tuned for standard water network Net3, currently requires knowledge and understanding of control list to decide manual splits
i = 0
for control_name, control in wn._controls.items():
    if verbose:
            print(control_name + " : " + control.__str__())
            print(control.__str__())
            
    control_assign = wn.get_control(control_name)
    if(i<=13):
        control_assign.assign_cps("PLC1") #does not create an actual CPS node by the name of SCADA1, simply creates a label which can be used as reference against the CPS control node registry
    else:
        control_assign.assign_cps("PLC2")
    i+=1

## ICS NETWORK CREATION: Manual creation of PLC and SCADA CPS_node tags and ownership assignments, as well as edge designations         
wn._cps_reg.add_PLC("PLC1")
wn._cps_reg.add_PLC("PLC2")
wn._cps_reg.add_SCADA("SCADA1")
wn._cps_reg["SCADA1"].add_owned("PLC1")
wn._cps_reg["SCADA1"].add_owned("PLC2")
wn._cps_reg.add_RTU("RTU1")
wn._cps_reg.add_RTU("RTU2")

#plc-to-SCADA edges and RTU-to-SCADA edges
wn._cps_edges.add_MODBUS("s1_MOD_p1","SCADA1","PLC1")
wn._cps_edges.add_MODBUS("s1_MOD_p2","SCADA1","PLC2")
wn._cps_edges.add_SER("r1_SER_p1","RTU1","PLC1")
wn._cps_edges.add_SER("r2_SER_p2","RTU2","PLC2")

#plc-to-plc edge added for duplication/connectivity
wn._cps_edges.add_MODBUS("p1_MOD_p2","PLC1","PLC2")
wn._cps_edges.add_SER("r1_SER_p2","RTU1","PLC2")
wn._cps_edges.add_SER("r2_SER_p1","RTU2","PLC1")

########### WN2 SETUP ###########
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

#plc-to-SCADA edges and RTU-to-SCADA edges
wn2._cps_edges.add_MODBUS("s1_MOD_p1","SCADA1","PLC1")
wn2._cps_edges.add_MODBUS("s1_MOD_p2","SCADA1","PLC2")
wn2._cps_edges.add_SER("r1_SER_p1","RTU1","PLC1")
wn2._cps_edges.add_SER("r2_SER_p2","RTU2","PLC2")

#plc-to-plc edge added for duplication/connectivity
wn2._cps_edges.add_MODBUS("p1_MOD_p2","PLC1","PLC2")
wn2._cps_edges.add_SER("r1_SER_p2","RTU1","PLC2")
wn2._cps_edges.add_SER("r2_SER_p1","RTU2","PLC1")


############ Simulate hydraulics baseline (WNTR) ############

wn.options.time.hydraulic_timestep = 3600
wn.options.time.duration = 48 * 3600 #new time of 30hr to allow for tank manipulation effect to propogate across time
sim1 = wntr.sim.WNTRSimulator(wn)
res1 = sim1.run_sim()

############ Simulate hydraulics (WNTR stepped) ############

# 24 hour simulation done in 1 x 12-hour chunk, 12 x 1-hour chunks

##### ATTACK ON PUMP 10: Disabling of control activating pump at set time #####
ctl_store = OrderedDict()
if wn2._controls.get("control 3") != None:
    ctl_store["control 3"] = wn2.get_control("control 3")
    wn2._cps_reg["PLC1"].disable_control("control 3")
    print("Control 3 deleted.")
#simulate first 24 hours
wn2.options.time.duration = 20 * 3600
sim2 = wntr.sim.WNTRSimulator(wn2)
res2 = sim2.run_sim()
wn2.options.time.pattern_start = wn2.options.time.pattern_start + (20 * 3600)
print(res2.node['head'])
wn2.set_initial_conditions(res2)


############ SPIN UP COMMUNICATION CLIENT & SERVERS ############

# initial run (first timestep, set up the results object) 
# spin up modbus server for PLC1
# parse args
parser = argparse.ArgumentParser()
parser.add_argument('-H', '--host', type=str, default='localhost', help='Host (default: localhost)')
parser.add_argument('-p', '--port', type=int, default=502, help='TCP port (default: 502)')
args = parser.parse_args()
# init modbus servers and start them: one server for each client system you want storing data and sending traffic to SCADA & attacker nodes
server = ModbusServer(host='127.0.0.1', port=args.port, no_block=True)
server.start()
server2 = ModbusServer(host='127.0.0.2', port=503, no_block=True) #note that this is necessary for running servers simultaneously on the same host-- VM/docker instances could run separate sim ports
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

############ STEPWISE RUN W/ TRAFFIC AND ATTACK INTEGRATION START ############
server.data_bank.set_holding_registers(0x0000,(res2.node["head"].iloc[12,:])*1e3)
print("Check MODBUS holding registers following 12hr runtime and regset: ")
c.open()
print(numpy.array(c.read_holding_registers(0x0000,97), dtype=numpy.float32)*1e-3)
res_groundTruth = res2.deep_copy()
res3 = res2.deep_copy()
c.close()
#simulate 28 hours in 28 1-hour chunks
for i in range(28):
    curr_t = 20+i+1
    wn2.options.time.duration = 1 * 3600
    res3 = res3.append(sim2.run_sim(prev_results=res_groundTruth), overwrite=False)
    res_groundTruth.append(res3, overwrite=False) #keep unmodified values 
    server.data_bank.set_holding_registers(0x0000,(res3.node["head"].iloc[curr_t,:])*1e3) #store head values
    server.data_bank.set_holding_registers(0x0061,(res3.node["pressure"].iloc[curr_t,:])*1e3) #store pressure values
    c2.open()
    if verbose:
        print("Pulled MODBUS holding registers following {time} hr runtime and regset: {open} ".format(time = curr_t, open = c2.is_open))
    flag = False
    if i >= 0: #at 24hr into simulation, start overwriting head values for tank1 to cause tank to continue to drain when possible
        h = numpy.array(c2.read_holding_registers(0x0000,97), dtype=numpy.float32)*1e-3 #read head values
        p = numpy.array(c2.read_holding_registers(0x0061,97), dtype=numpy.float32)*1e-3 #read pressure values
        if (h[92]-39.96) < 5.21: #head(meters)-initial elevation; 5.21m = 17.1ft; 45.17m ~> 17.1ft relative head
            flag = True
            r = rand.gauss(0.1,0.03)
            nv = 45.17+r
            pv = 7.6+r
            if c2.write_single_register(0x005E,int(nv*1e3)): #overwrite t1 head at reg 94 (hex 5E) with incorrect head which would read as above switching level
                res3.node["head"].loc[(20+i+1)*3600,'1'] = nv #conditionally set backend values
                print("Head value tank 1 overwritten, showing open-valve levels")
                ############ MANUAL DRIFT/STATUS FIX: OVERWRITE PUMP STATUS TO 'CLOSED' ############
                if res3.link['status']['335'][curr_t*3600] == 1: 
                    res_groundTruth.link['status']['335'][curr_t*3600] = LinkStatus.Closed
                    #res_groundTruth.link['status']['60'][curr_t*3600] = LinkStatus.Closed
                    
                    if 'close pipe 335' not in wn2._controls:
                        pipe = wn2.get_link('335')        
                        act = wntr.network.controls.ControlAction(pipe, 'status', 
                                                                    wntr.network.LinkStatus.Closed)
                        cond = wntr.network.controls.SimTimeCondition(wn2, '>', '00:00:00')
                        ctrl = wntr.network.controls.Control(cond, act, priority=ControlPriority.very_high)
                        wn2.add_control('close pipe ' + '335', ctrl)
                    if 'close pipe 60' not in wn2._controls:
                        pipe = wn2.get_link('60')        
                        act = wntr.network.controls.ControlAction(pipe, 'status', 
                                                                    wntr.network.LinkStatus.Closed)
                        cond = wntr.network.controls.SimTimeCondition(wn2, '>', '00:00:00')
                        ctrl = wntr.network.controls.Control(cond, act, priority=ControlPriority.very_high)
                        wn2.add_control('close pipe ' + '60', ctrl)
                ####################################################################################    
            if c2.write_multiple_registers(0x0061,[int(pv*1e3)]): #overwrite t1 head with incorrect head which would read as safe
                res3.node["pressure"].loc[(20+i+1)*3600,'1'] = pv #conditionally set backend values
                print("Pressure value tank 1 overwritten, showing open-valve levels")
                if wn2._controls.get("control 15") != None:
                    ctl_store["control 15"] = wn2.get_control("control 15")
                    wn2._cps_reg["PLC2"].disable_control("control 15")
                    print("Control 15 deleted.")
                    if 'deactivate pump 335' not in wn2._controls:
                        pump = wn2.get_link('335')   
                        tank = wn2.get_node('1')     
                        act = wntr.network.controls.ControlAction(pump, 'status', 
                                                                    wntr.network.LinkStatus.Closed)
                        cond = wntr.network.controls.ValueCondition(tank, 'level', '>', '0.21208')
                        ctrl = wntr.network.controls.Control(cond, act, priority=ControlPriority.very_high)
                        wn2.add_control('deactivate pump 335', ctrl)
                # removed control: "IF TANK 1 LEVEL BELOW 5.21208 THEN PUMP 335 STATUS IS OPEN PRIORITY 3"
                if wn2._controls.get("control 17") != None:
                    ctl_store["control 17"] = wn2.get_control("control 17")
                    wn2._cps_reg["PLC2"].disable_control("control 17")
                    print("Control 17 deleted.")
                # removed control: "IF TANK 1 LEVEL BELOW 5.21208 THEN PIPE 330 STATUS IS CLOSED PRIORITY 3"

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
    res2.append(res3,overwrite=True)  #append tampered values
    wn2.set_initial_conditions(res_groundTruth, ts=3600)
    wn2.options.time.pattern_start = wn2.options.time.pattern_start + (1 * 3600)
    if(flag):
        wn2._link_reg['335'].initial_status = LinkStatus.Closed
        if wn2._controls.get("control 15") != None:
            ctl_store["control 15"] = wn2.get_control("control 15")
            wn2._cps_reg["PLC2"].disable_control("control 15")
            #print("Control 15 deleted.")
        # removed control: "IF TANK 1 LEVEL BELOW 5.21208 THEN PUMP 335 STATUS IS OPEN PRIORITY 3"
        if wn2._controls.get("control 17") != None:
            ctl_store["control 17"] = wn2.get_control("control 17")
            wn2._cps_reg["PLC2"].disable_control("control 17")
            #print("Control 17 deleted.")
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
res2H = res2.node['head'].loc[:,wn2.node_name_list]
print(res2H)
groundtruth = res_groundTruth.node['head'].loc[:,wn2.node_name_list]
#print(groundtruth)
headbase = resbase.node['head'].loc[:, wn_baseline.node_name_list]
#headbase = headbase * 3.28084 # Convert tank head to ft
res2H.index /= 3600 # convert time to hours
fig = px.line(res2H)
fig = fig.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
fig.write_html('CPS_Net3_Attack_MODBUS_T1_head_falseFeedback.html')

groundtruth.index /= 3600 # convert time to hours
figg = px.line(groundtruth)
figg = figg.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
figg.write_html('CPS_Net3_Attack_MODBUS_T1_head_groundTruth.html')

headbase.index /= 3600 # convert time to hours
figb = px.line(headbase)
figb = figb.update_layout(xaxis_title='Time (hr)', yaxis_title='Head (ft)',
                  template='simple_white', width=800, height=500)
figb.write_html('CPS_Net3_Baseline_head.html')

res2F335 = res2.link['flowrate']['335']
groundtruthF335 = res_groundTruth.link['flowrate']['335']

res2F10 = res2.link['flowrate']['10']
groundtruthF10 = res_groundTruth.link['flowrate']['10']

resbaseF335 = resbase.link['flowrate']['335']
resbaseF10 = resbase.link['flowrate']['10']

res2F335.index /= 3600 # convert time to hours
figresF335 = px.line(res2F335)
figresF335 = figresF335.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figresF335.write_html('CPS_Net3_Attack_MODBUS_res2_flowrate_335.html')

groundtruthF335.index /= 3600 # convert time to hours
figgtF335 = px.line(groundtruthF335)
figgtF335 = figgtF335.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figgtF335.write_html('CPS_Net3_Attack_MODBUS_gt_flowrate_335.html')


res2F10.index /= 3600 # convert time to hours
figresF10 = px.line(res2F10)
figresF10 = figresF10.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figresF10.write_html('CPS_Net3_Attack_MODBUS_res2_flowrate_10.html')

groundtruthF10.index /= 3600 # convert time to hours
figgtF10 = px.line(groundtruthF10)
figgtF10 = figgtF10.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figgtF10.write_html('CPS_Net3_Attack_MODBUS_gt_flowrate_10.html')


resbaseF10.index /= 3600 # convert time to hours
figresbaseF10 = px.line(resbaseF10)
figresbaseF10 = figresbaseF10.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figresbaseF10.write_html('CPS_Net3_Attack_MODBUS_resbase_flowrate_10.html')

resbaseF335.index /= 3600 # convert time to hours
figresbaseF335 = px.line(resbaseF335)
figresbaseF335 = figresbaseF335.update_layout(xaxis_title='Time (hr)', yaxis_title='Flowrate (cms)',
                  template='simple_white', width=800, height=500)
figresbaseF335.write_html('CPS_Net3_Attack_MODBUS_resbase_flowrate_335.html')