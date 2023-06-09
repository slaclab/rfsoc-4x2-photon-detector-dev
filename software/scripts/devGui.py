#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# This file is part of the 'rfsoc-4x2-photon-detector-dev'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'rfsoc-4x2-photon-detector-dev', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------
import setupLibPaths
import rfsoc_4x2_photon_detector_dev

import os
import sys
import argparse
import importlib
import rogue
import axi_soc_ultra_plus_core.rfsoc_utility.pydm

if __name__ == "__main__":

#################################################################

    # Set the argument parser
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument(
        "--ip",
        type     = str,
        required = False,
        default  = '10.0.0.10',
        help     = "ETH Host Name (or IP address)",
    )

    parser.add_argument(
        "--defaultFile",
        type     = str,
        required = False,
        default  = 'config/defaults.yml',
        help     = "Sets the default YAML configuration file to be loaded at the root.start()",
    )

    # Get the arguments
    args = parser.parse_args()

    #################################################################

    top_level = os.path.realpath(__file__).split('software')[0]
    ui = top_level+'firmware/submodules/axi-soc-ultra-plus-core/python/axi_soc_ultra_plus_core/rfsoc_utility/gui/GuiTop.py'

    #################################################################

    with rfsoc_4x2_photon_detector_dev.Root(
        ip          = args.ip,
        defaultFile = args.defaultFile,
    ) as root:
        axi_soc_ultra_plus_core.rfsoc_utility.pydm.runPyDM(
            serverList = root.zmqServer.address,
            ui         = ui,
            sizeX      = 800,
            sizeY      = 800,
            numAdcCh   = 1,
            numDacCh   = 1,
        )
    #################################################################
