"""
The following test shows the automatic generation of a simple cps network for a hydraulic network based on the control set
"""
import wntr
from wntr.network.CPS_node import SCADA, PLC, RTU, MODBUS, EIP, SER, CPSNodeRegistry, CPSEdgeRegistry
import wntr.network.io
from wntr.network.controls import ValueCondition, RelativeCondition
import wntr.metrics.topographic
from wntr.network.layer import autogenerate_full_cps_layer
import plotly.express as px


# Create a water network model
inp_file = '../networks/Net6.inp'
wn_controller = wntr.network.WaterNetworkModel(inp_file)
# Generate a CPS layer     
autogenerate_full_cps_layer(wn_controller, placement_type='complex', timed_control_assignments='local', edge_types='MODBUS', verbose=0)
# Test the CPS layer's connectivity
cpsG = wn_controller.cps_to_graph()
print(wntr.metrics.topographic.algebraic_connectivity(cpsG))
print(wntr.metrics.topographic.spectral_gap(cpsG))
# Test the water network model 
sim_1 = wntr.sim.EpanetSimulator(wn_controller)
results_1 = sim_1.run_sim()      
