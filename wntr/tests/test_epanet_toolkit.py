import unittest
from os.path import abspath, dirname, join, exists

import wntr.epanet.toolkit

testdir = dirname(abspath(__file__))
datadir = join(testdir, "..", "..", "examples", "networks")


class TestEpanetToolkit(unittest.TestCase):
    
    def test_isOpen(self):
        enData = wntr.epanet.toolkit.ENepanet()
        enData.inpfile = join(datadir, "Net1.inp")
        self.assertEqual(0, enData.isOpen())
        enData.ENopen(enData.inpfile, "temp.rpt")
        self.assertEqual(1, enData.isOpen())

    def test_ENgetcount(self):
        enData = wntr.epanet.toolkit.ENepanet()
        enData.inpfile = join(datadir, "Net1.inp")
        enData.ENopen(enData.inpfile, "temp.rpt")
        
        nNodes = enData.ENgetcount(wntr.epanet.util.EN.NODECOUNT)
        self.assertEqual(11, nNodes)
        nLinks = enData.ENgetcount(wntr.epanet.util.EN.LINKCOUNT)
        self.assertEqual(13, nLinks)
    
    def test_ENgetflowunits(self):
        enData = wntr.epanet.toolkit.ENepanet()
        enData.inpfile = join(datadir, "Net1.inp")
        enData.ENopen(enData.inpfile, "temp.rpt")
        
        flowunit = enData.ENgetflowunits()
        assert(flowunit==1) # GPM
        
    def test_ENgetindex_ENgetvalue(self):
        enData = wntr.epanet.toolkit.ENepanet()
        enData.inpfile = join(datadir, "Net1.inp")
        enData.ENopen(enData.inpfile, "temp.rpt")
        
        node_index = enData.ENgetnodeindex('10') 
        assert(node_index == 1) 
        node_val = enData.ENgetnodevalue(node_index, 0) # ELEVATION = 0
        assert(node_val == 710) 
        
        link_index = enData.ENgetlinkindex('11') 
        assert(link_index == 2) 
        link_val = enData.ENgetlinkvalue(link_index, 0) # DIAMETER = 0
        assert(link_val == 14) 
    
    def test_ENsaveinpfile(self):
        enData = wntr.epanet.toolkit.ENepanet()
        enData.inpfile = join(datadir, "Net1.inp")
        enData.ENopen(enData.inpfile, "temp.rpt")
        
        enData.ENsaveinpfile("Net1_toolkit.inp") 
        file_exists = exists("Net1_toolkit.inp")
        assert file_exists
        
    def test_runepanet(self):
        inpfile = join(datadir, "Net1.inp")
        wntr.epanet.toolkit.runepanet(inpfile)
        
        reader = wntr.epanet.io.BinFile()
        results = reader.read("temp.bin")
        
        assert(isinstance(results, wntr.sim.results.SimulationResults))

if __name__ == "__main__":
    unittest.main()
