import unittest
from os.path import abspath, dirname, join
import wntr


testdir = dirname(abspath(str(__file__)))
test_datadir = join(testdir, "networks_for_testing")
ex_datadir = join(testdir, "..", "..", "examples", "networks")


tolerances = {
    "flowrate": 1.0e-5, # 10 mL/s
    "velocity": 1.0e-2, # 0.01 m/s
    "demand": 1.0e-4, # 10 mL/s
    "head": 1.0e-2,  # 0.01 m
    "pressure": 1.0e-2,  # 0.01 m H2O
    "headloss": 1.0e-2,  # 0.01 
    "status": 0.5,  #  i.e., 0 since this is integer
    "setting": 1.0e-2,  # 0.01
}

class TestStopStartSim(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        inp_file = join(ex_datadir, "Net3.inp")
        simulator = wntr.sim.WNTRSimulator
        
        # straight 24 hour simulation
        self.wn = wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.time.hydraulic_timestep = 3600
        self.wn.options.time.duration = 24 * 3600
        sim = simulator(self.wn)
        self.res1 = sim.run_sim(solver_options={"TOL": 1e-8})
        
        # 24 hour simulation done in one 10 hour chunk and one 14 hour chunk
        self.wn = wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.time.hydraulic_timestep = 3600
        self.wn.options.time.duration = 10 * 3600
        sim = simulator(self.wn)
        self.res2 = sim.run_sim(solver_options={'TOL':1e-8})
        self.wn.set_initial_conditions(self.res2)
        self.wn.options.time.pattern_start = self.wn.options.time.pattern_start + 10 * 3600
        self.wn.options.time.duration = 14 * 3600
        sim = simulator(self.wn)
        self.res3 = sim.run_sim(solver_options={'TOL':1e-8})
        self.res3._adjust_time(10*3600)
        self.res2.append(self.res3)
        self.res4 = abs(self.res1 - self.res2).max()

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_nodes(self):
        node_keys = ["demand", "head", "pressure"]
        for key in node_keys:
            max_res_diff = self.res4.node[key].max()
            self.assertLess(max_res_diff, tolerances[key])
            
    def test_links(self):
        link_keys = ["flowrate", "velocity", "status", "setting"]
        for key in link_keys:
            max_res_diff = self.res4.link[key].max()
            self.assertLess(max_res_diff, tolerances[key])


class TestStopStartEpanetSim(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        inp_file = join(ex_datadir, "Net3.inp")
        
        # straight 24 hour simulation
        self.wn = wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.time.hydraulic_timestep = 3600
        self.wn.options.time.duration = 24 * 3600
        sim = wntr.sim.EpanetSimulator(self.wn)
        self.res1 = sim.run_sim()
        
        # 24 hour simulation done in one 10 hour chunk and one 14 hour chunk
        self.wn = wntr.network.WaterNetworkModel(inp_file)
        self.wn.options.time.hydraulic_timestep = 3600
        self.wn.options.time.duration = 10 * 3600
        sim = wntr.sim.EpanetSimulator(self.wn)
        self.res2 = sim.run_sim()
        self.wn.set_initial_conditions(self.res2)
        self.wn.options.time.pattern_start = self.wn.options.time.pattern_start + 10 * 3600
        self.wn.options.time.duration = 14 * 3600
        sim = wntr.sim.EpanetSimulator(self.wn)
        self.res3 = sim.run_sim()
        self.res3._adjust_time(10*3600)
        
        self.res2.append(self.res3)
        self.res4 = abs(self.res1 - self.res2).max()

    @classmethod
    def tearDownClass(self):
        pass
    
    def test_nodes(self):
        node_keys = ["demand", "head", "pressure"]
        for key in node_keys:
            max_res_diff = self.res4.node[key].max()
            self.assertLess(max_res_diff, tolerances[key])
            
    def test_links(self):
        link_keys = ["flowrate", "velocity", "status", "setting", "headloss"]
        for key in link_keys:
            max_res_diff = self.res4.link[key].max()
            self.assertLess(max_res_diff, tolerances[key])


if __name__ == "__main__":
    unittest.main()