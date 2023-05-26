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

import axi_soc_ultra_plus_core.rfsoc_utility as rfsoc_utility
import rfsoc_4x2_photon_detector_dev as rfsoc

class Application(pr.Device):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.add(rfsoc_utility.AppRingBuffer(
            offset   = 0x00_000000,
            numAdcCh = 1, # Must match NUM_ADC_CH_G config
            numDacCh = 1, # Must match NUM_DAC_CH_G config
            # expand   = True,
        ))

        self.add(rfsoc_utility.SigGen(
            name         = 'DacSigGen',
            offset       = 0x01_000000,
            numCh        = 1,  # Must match NUM_CH_G config
            ramWidth     = 9,  # Must match RAM_ADDR_WIDTH_G config
            smplPerCycle = 16, # Must match SAMPLE_PER_CYCLE_G config
            # expand       = True,
        ))

        self.add(rfsoc.SigGenLoader(
            name      = 'SigGenLoader',
            DacSigGen = self.DacSigGen,
            expand    = True,
        ))

        self.add(pr.RemoteVariable(
            name         = 'StartDacFlag',
            offset       = 0x02_000100,
            bitSize      = 1,
            bitOffset    = 0,
            base         = pr.UInt,
            hidden       = True,
        ))

        self.add(pr.LocalVariable(
            name  = 'EnableSoftTrig',
            mode  = 'RW',
            value = True,
        ))

        @self.command(description  = 'Force a DAC signal generator trigger from software')
        def getWaveformBurst():
            if self.EnableSoftTrig.get():
                self.StartDacFlag.set(1)
                self.StartDacFlag.set(0)

        self.add(pr.LocalVariable(
            name         = 'GetWaveformBurst',
            mode         = 'RO',
            localGet     = self.getWaveformBurst,
            pollInterval = 1,
            hidden       = True,
        ))

