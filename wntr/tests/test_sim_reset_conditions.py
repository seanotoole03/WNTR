import unittest
import warnings
from os.path import abspath, dirname, join

import matplotlib.pylab as plt
import wntr

testdir = dirname(abspath(str(__file__)))
test_datadir = join(testdir, "networks_for_testing")
ex_datadir = join(testdir, "..", "..", "examples", "networks")

### These tests need to be updated to be real tests, not graphics and use additional networks


def ignore_warnings(test_func):
    """
    Decorator function to supress warnings when using a (test) function.

    Source: "How to Suppress Python unittest Warnings". Tony Podlaski. Blog Post
    URL: https://www.neuraldump.net/2017/06/how-to-suppress-python-unittest-warnings/
    Accessed: 2021-04-07
    """

    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            test_func(self, *args, **kwargs)

    return do_test


class Test_Reset_Conditions(unittest.TestCase):
    @classmethod
    def setUpClass(self):

        self.inp_file = join(ex_datadir, "Net3.inp")
        wn = wntr.network.WaterNetworkModel(self.inp_file)

        wn.options.time.duration = 100 * 3600
        sim = wntr.sim.EpanetSimulator(wn)
        self.benchmarck_results = sim.run_sim(reset_intial_conditions=False)

        plt.figure()
        ax = plt.gca()
        self.benchmarck_results.node["pressure"].plot(ax=ax, title="Benchmark")

    @classmethod
    def tearDownClass(self):
        pass

    def test_epanetsim_continue(self):

        plt.figure()
        ax = plt.gca()

        wn = wntr.network.WaterNetworkModel(self.inp_file)

        sim = wntr.sim.EpanetSimulator(wn)

        wn.options.time.duration = 12 * 3600
        results1 = sim.run_sim(reset_intial_conditions=False)
        results1.node["pressure"].plot(ax=ax)

        wn.options.time.duration = 56 * 3600
        results2 = sim.run_sim(reset_intial_conditions=False)
        results2.node["pressure"].plot(ax=ax)

        wn.options.time.duration = 100 * 3600
        results3 = sim.run_sim(reset_intial_conditions=False)
        results3.node["pressure"].plot(ax=ax, title="EPANETsim_continue")

    @ignore_warnings
    def test_wntrsim_continue(self):

        plt.figure()
        ax = plt.gca()

        wn = wntr.network.WaterNetworkModel(self.inp_file)

        sim = wntr.sim.WNTRSimulator(wn)

        wn.options.time.duration = 12 * 3600
        results1 = sim.run_sim(reset_intial_conditions=False)
        results1.node["pressure"].plot(ax=ax)

        wn.options.time.duration = 56 * 3600
        results2 = sim.run_sim(reset_intial_conditions=False)
        results2.node["pressure"].plot(ax=ax)

        wn.options.time.duration = 100 * 3600
        wn.write_inpfile("Net3_epanet.inp")

        results3 = sim.run_sim(reset_intial_conditions=False)
        results3.node["pressure"].plot(ax=ax, title="WNTRSim_continue")

    def test_epanetsim_reset(self):

        plt.figure()
        ax = plt.gca()

        wn = wntr.network.WaterNetworkModel(self.inp_file)

        sim = wntr.sim.EpanetSimulator(wn)

        wn.options.time.duration = 100 * 3600
        results1 = sim.run_sim(reset_intial_conditions=True)
        results1.node["pressure"].plot(ax=ax, title="EPANETsim_reset1")

        plt.figure()
        ax = plt.gca()

        wn.options.time.duration = 100 * 3600
        results2 = sim.run_sim(reset_intial_conditions=True)
        results2.node["pressure"].plot(ax=ax, title="EPANETsim_reset2")

    @ignore_warnings
    def test_wntrsim_reset(self):

        plt.figure()
        ax = plt.gca()

        wn = wntr.network.WaterNetworkModel(self.inp_file)

        sim = wntr.sim.WNTRSimulator(wn)

        wn.options.time.duration = 100 * 3600
        results1 = sim.run_sim(reset_intial_conditions=True)
        results1.node["pressure"].plot(ax=ax, title="WNTRsim_reset1")

        plt.figure()
        ax = plt.gca()

        wn.options.time.duration = 100 * 3600
        results2 = sim.run_sim(reset_intial_conditions=True)
        results2.node["pressure"].plot(ax=ax, title="WNTRsim_reset2")

    # def test_both_continue(self):

    #     plt.figure()
    #     ax = plt.gca()

    #     wn = wntr.network.WaterNetworkModel(self.inp_file)

    #     sim = wntr.sim.WNTRSimulator(wn)
    #     wn.options.time.duration = 12*3600
    #     results1 = sim.run_sim(reset_intial_conditions=False)
    #     results1.node['pressure'].plot(ax=ax)

    #     sim = wntr.sim.EpanetSimulator(wn)
    #     wn.options.time.duration = 56*3600
    #     results2 = sim.run_sim(reset_intial_conditions=False)
    #     results2.node['pressure'].plot(ax=ax)

    #     sim = wntr.sim.WNTRSimulator(wn)
    #     wn.options.time.duration = 100*3600
    #     results3 = sim.run_sim(reset_intial_conditions=False)
    #     results3.node['pressure'].plot(ax=ax, title='Switch_combo')


if __name__ == "__main__":
    unittest.main(verbosity=2)
