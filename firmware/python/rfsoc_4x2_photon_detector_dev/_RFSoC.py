#-----------------------------------------------------------------------------
# This file is part of the 'rfsoc-4x2-photon-detector-dev'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'rfsoc-4x2-photon-detector-dev', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import pyrogue as pr

import axi_soc_ultra_plus_core  as socCore
import surf.xilinx              as xil
import rfsoc_4x2_photon_detector_dev as rfsoc

class RFSoC(pr.Device):
    def __init__(self,top_level='',**kwargs):
        super().__init__(**kwargs)

        self.add(socCore.AxiSocCore(
            offset      = 0x0000_0000,
            numDmaLanes = 2,
        ))

        self.add(xil.RfDataConverter(
            offset = 0x9000_0000,
        ))

        self.add(rfsoc.Application(
            offset    = 0xA000_0000,
            top_level = top_level,
            expand    = True,
        ))
