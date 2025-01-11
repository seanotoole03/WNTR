import unittest
from os.path import abspath, dirname, join

import pandas as pd
import wntr
from pandas.testing import assert_frame_equal
from wntr.network.controls import Control, Rule
from wntr.network.CPS_node import SCADA, PLC, RTU, MODBUS, EIP, SER, CPSNodeRegistry, CPSEdgeRegistry
from wntr.network.layer import autogenerate_full_cps_layer
import argparse
from pyModbusTCP.server import ModbusServer, DataHandler
from pyModbusTCP.constants import EXP_ILLEGAL_FUNCTION
from pyModbusTCP.client import ModbusClient

import random as rand

import pycomm3
import serial

testdir = dirname(abspath(str(__file__)))
test_datadir = join(testdir, "networks_for_testing")
ex_datadir = join(testdir, "..", "..", "examples", "networks")


class TestValveLayer(unittest.TestCase):
    @classmethod
    def setUpClass(self):

        inp_file = join(ex_datadir, "Net3.inp")
        self.wn = wntr.network.WaterNetworkModel(inp_file)

    @classmethod
    def tearDownClass(self):
        pass

    def test_valve_layer_random(self):

        valves = wntr.network.generate_valve_layer(self.wn, "random", 40, 123)

        # valves.to_csv('valve_layer_random.csv')
        # ax = wntr.graphics.plot_network(self.wn, node_size=7, valve_layer=valves,
        #                                          title='Random, 40')

        expected = pd.read_csv(
            join(test_datadir, "valve_layer_random.csv"), index_col=0, dtype="object"
        )

        assert_frame_equal(valves, expected)

    def test_valve_layer_strategic(self):

        # Compute the expected number of valves for N-0, N-1, N-2, N-3, N-4
        G = self.wn.to_graph()
        node_degree = pd.Series(dict(G.degree()))
        expected_n_valves = pd.Series(index=[4, 3, 2, 1, 0])
        for N in [4, 3, 2, 1, 0]:
            expected_n_valves[N] = node_degree[node_degree > N].shape[0]

        expected_n_valves = expected_n_valves.cumsum()

        for N in [0, 1, 2, 3, 4]:

            valves = wntr.network.generate_valve_layer(self.wn, "strategic", N, 123)

            # valves.to_csv('valve_layer_stategic_'+str(N)+'.csv')
            # ax = wntr.graphics.plot_network(self.wn, node_size=7, valve_layer=valves,
            #                                          title='Strategic, '+str(N))

            expected_valves = pd.read_csv(
                join(test_datadir, "valve_layer_stategic_" + str(N) + ".csv"),
                index_col=0,
                dtype="object",
            )

            self.assertEqual(valves.shape[0], expected_n_valves[N])
            assert_frame_equal(valves, expected_valves, check_index_type=False)


class TestCPSLayer(unittest.TestCase):
    @classmethod
    def setUpClass(self):

        inp_file = join(ex_datadir, "Net6.inp")
        self.wn = wntr.network.WaterNetworkModel(inp_file)
        
    @classmethod
    def tearDownClass(self):
        pass

    def test_CPS_layer_simple(self):
        # generate a simple cps_layer
        cps_layer = autogenerate_full_cps_layer(self.wn, placement_type='simple', timed_control_assignments='local', edge_types='MODBUS', n=2, verbose=1)

        expected = pd.read_csv(
            join(test_datadir, "net6_autogen_simple_local_MODBUS_2.csv"), index_col=0, dtype="object"
        )

        assert_frame_equal(cps_layer, expected)

    def test_CPS_layer_complex(self):

        cps_layer = autogenerate_full_cps_layer(self.wn, placement_type='complex', timed_control_assignments='local', edge_types='MODBUS', n=2, verbose=1)

        expected = pd.read_csv(
            join(test_datadir, "net6_autogen_complex_local_MODBUS_2.csv"), index_col=0, dtype="object"
        )

        assert_frame_equal(cps_layer, expected)


if __name__ == "__main__":
    unittest.main()
