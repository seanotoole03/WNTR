<h1>
<img src="https://raw.githubusercontent.com/usepa/wntr/main/documentation/_static/logo.jpg" width="375">
</h1><br>
[![build](https://github.com/seanotoole03/WNTR/actions/workflows/build_tests.yml/badge.svg)](https://github.com/seanotoole03/WNTR/actions/workflows/build_tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/seanotoole03/WNTR/badge.svg?branch=main)](https://coveralls.io/github/seanotoole03/WNTR?branch=main)
[![docs](https://github.com/seanotoole03/WNTR/actions/workflows/build_deploy_pages.yml/badge.svg)](https://github.com/seanotoole03/WNTR/actions/workflows/build_deploy_pages.yml)

WNTR+CPS Fork Information
--------------
This fork of the USEPA WNTR project is an experimental branch worked on as part of research collaboration 
between Boise State University and Sandia National Labs focusing on representation of 
Cyber-physical Systems (CPS) within water distribution networks. The capabilities introduced by the components
introduced in this module may not have full test coverage, but the developer will attempt to address any bugs or 
errors as they are reported, and add corresponding tests as necessary.

Core WNTR Information
--------------
The Water Network Tool for Resilience (WNTR) is a Python package designed to simulate and 
analyze resilience of water distribution networks. The software includes capability to:

* Generate water network models
* Modify network structure and operations
* Add disruptive events including pipe leaks
* Add response/repair strategies
* Simulate pressure dependent demand and demand-driven hydraulics
* Simulate water quality 
* Evaluate resilience 
* Visualize results

For more information, go to https://usepa.github.io/WNTR/ 

WNTR+CPS Additional Functionality
--------------
This software package includes additional capabilities to those listed above:
* Simulate CPS network creation and authority hierarchies
* Estimate CPS network resilience using spectral gap and connectivity
* Assign network controls and modify or delete controls through CPS node functions
* Automatically generate CPS networks based on hydraulic network models
* 2025 v1 WNTRGoop release adds initial demonstration of use of WNTR+CPS and python-based MODBUS, EIP, Serial traffic generation modules in replicating/paralleling the 2024 Ukraine FrostyGoop attacks

Installation
--------------

The latest release of WNTR+CPS can only be installed manually from this codebase, and requires running in a virtual environment to overwrite core WNTR library functions it has modified.


Citing WNTR+CPS
-----------------

To cite WNTR, use one of the following references:

* Klise, K.A., Hart, D.B., Bynum, M., Hogge, J., Haxton, T., Murray, R., Burkhardt, J. (2020). Water Network Tool for Resilience (WNTR) User Manual: Version 0.2.3. U.S. EPA Office of Research and Development, Washington, DC, EPA/600/R-20/185, 82p.

* Klise, K.A., Murray, R., Haxton, T. (2018). An overview of the Water Network Tool for Resilience (WNTR), In Proceedings of the 1st International WDSA/CCWI Joint Conference, Kingston, Ontario, Canada, July 23-25, 075, 8p.

* Klise, K.A., Bynum, M., Moriarty, D., Murray, R. (2017). A software framework for assessing the resilience of drinking water systems to disasters with an example earthquake case study, Environmental Modelling and Software, 95, 420-431, doi: 10.1016/j.envsoft.2017.06.022

To cite WNTR+CPS, use one of the following references:

-- publication data pending conference proceedings --

License
------------

WNTR+CPS is released under the Revised BSD license. See 
[LICENSE.md](https://github.com/USEPA/WNTR/blob/main/LICENSE.md) for more details.

Organization
------------

Directories
  * wntr - Python package
  * documentation - User manual
  * examples - Examples and network files
  
Contact
--------

   * Sean O'Toole, Boise State University seanotoole@u.boisestate.edu

