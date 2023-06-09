#-----------------------------------------------------------------------------
# This file is part of the 'rfsoc-4x2-photon-detector-dev'. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the 'rfsoc-4x2-photon-detector-dev', including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
#-----------------------------------------------------------------------------

import time

import rogue
import rogue.interfaces.stream as stream
import rogue.utilities.fileio
import rogue.hardware.axi
import rogue.interfaces.memory

import pyrogue as pr
import pyrogue.protocols
import pyrogue.utilities.fileio
import pyrogue.protocols.epicsV4

import rfsoc_4x2_photon_detector_dev as rfsoc
import axi_soc_ultra_plus_core.rfsoc_utility as rfsoc_utility
import axi_soc_ultra_plus_core.hardware.RealDigitalRfSoC4x2 as rfsoc_hw
import axi_soc_ultra_plus_core as soc_core

rogue.Version.minVersion('6.0.0')

class Root(pr.Root):
    def __init__(self,
            ip           = '10.0.0.10', # ETH Host Name (or IP address)
            top_level    = '',
            defaultFile  = 'config/defaults.yml',
            lmkConfig    = 'config/lmk/HexRegisterValues.txt',
            lmxConfig    = 'config/lmx/HexRegisterValues.txt',
            epics_enable = False,
            epics_prefix = 'rfsoc_ioc',
            zmqSrvEn     = True,  # Flag to include the ZMQ server
            **kwargs):
        super().__init__(**kwargs)

        #################################################################
        if zmqSrvEn:
            self.zmqServer = pyrogue.interfaces.ZmqServer(root=self, addr='*', port=0)
            self.addInterface(self.zmqServer)
        #################################################################

        # Local Variables
        self.epics_enable = epics_enable
        self.epics_prefix = epics_prefix
        self.top_level    = top_level
        if self.top_level != '':
            self.defaultFile = f'{top_level}/{defaultFile}'
            self.lmkConfig   = f'{top_level}/{lmkConfig}'
            self.lmxConfig   = f'{top_level}/{lmxConfig}'
        else:
            self.defaultFile = defaultFile
            self.lmkConfig   = lmkConfig
            self.lmxConfig   = lmxConfig

        # File writer
        self.dataWriter = pr.utilities.fileio.StreamWriter()
        self.add(self.dataWriter)

        ##################################################################################
        ##                              Register Access
        ##################################################################################

        # Check if we can ping the device and TCP socket not open
        soc_core.connectionTest(ip)

        # Start a TCP Bridge Client, Connect remote server at 'ethReg' ports 9000 & 9001.
        self.memMap = rogue.interfaces.memory.TcpClient(ip,9000)


        # Add RfSoC4x2 PS hardware control
        self.add(rfsoc_hw.Hardware(
            memBase    = self.memMap,
        ))

        # Added the RFSoC device
        self.add(rfsoc.RFSoC(
            memBase    = self.memMap,
            offset     = 0x04_0000_0000, # Full 40-bit address space
            top_level  = self.top_level,
            expand     = True,
        ))

        ##################################################################################
        ##                              Data Path
        ##################################################################################

        # Create rogue stream arrays
        self.ringBufferAdc = [stream.TcpClient(ip,10000+2*(i+0))  for i in range(1)]
        self.ringBufferDac = [stream.TcpClient(ip,10000+2*(i+16)) for i in range(1)]

        self.adcRateDrop   = [stream.RateDrop(True,1.0) for i in range(1)]
        self.dacRateDrop   = [stream.RateDrop(True,1.0) for i in range(1)]

        self.adcProcessor  = [rfsoc_utility.RingBufferProcessor(name=f'AdcProcessor[{i}]',sampleRate=2.032E+9,maxSize=4*2**9)  for i in range(1)]
        self.dacProcessor  = [rfsoc_utility.RingBufferProcessor(name=f'DacProcessor[{i}]',sampleRate=8.128E+9,maxSize=16*2**9) for i in range(1)]

        self.pvAdc = [rfsoc_utility.RingBufferProcessor(name=f'PvAdc[{i}]',sampleRate=2.032E+9,maxSize=4*2**9, liveDisplay=False) for i in range(1)]
        self.pvDac = [rfsoc_utility.RingBufferProcessor(name=f'PvDac[{i}]',sampleRate=8.128E+9,maxSize=16*2**9,liveDisplay=False) for i in range(1)]

        # Connect the rogue stream arrays: ADC/DAC Ring Buffer Path
        for i in range(1):

            self.ringBufferAdc[i] >> self.dataWriter.getChannel(i+0)
            self.ringBufferAdc[i] >> self.adcRateDrop[i] >> self.adcProcessor[i]
            self.add(self.adcProcessor[i])

            self.ringBufferAdc[i] >> self.pvAdc[i]
            self.add(self.pvAdc[i])

            self.ringBufferDac[i] >> self.dataWriter.getChannel(i+16)
            self.ringBufferDac[i] >> self.dacRateDrop[i] >> self.dacProcessor[i]
            self.add(self.dacProcessor[i])

            self.ringBufferDac[i] >> self.pvDac[i]
            self.add(self.pvDac[i])

        ##################################################################################
        ##                              EPICS Path
        ##################################################################################

        if self.epics_enable:

            self.pv_map = {
                # AxiVersion variables
                'Root.RFSoC.AxiSocCore.AxiVersion.FpgaVersion' : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:FpgaVersion',
                'Root.RFSoC.AxiSocCore.AxiVersion.ScratchPad'  : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:ScratchPad',
                'Root.RFSoC.AxiSocCore.AxiVersion.UpTimeCnt'   : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:UpTimeCnt',
                'Root.RFSoC.AxiSocCore.AxiVersion.UpTime'      : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:UpTime',
                'Root.RFSoC.AxiSocCore.AxiVersion.GitHash'     : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:GitHash',
                'Root.RFSoC.AxiSocCore.AxiVersion.BuildStamp'  : f'{epics_prefix}:Root:RFSoC:AxiSocCore:AxiVersion:BuildStamp',

                # General application variables
                'Root.RFSoC.Application.EnableSoftTrig'  : f'{epics_prefix}:Root:RFSoC:Application:EnableSoftTrig',
                'Root.RFSoC.Application.StartDacFlag'    : f'{epics_prefix}:Root:RFSoC:Application:StartDacFlag',

                # DAC SiPM Waveform Loader
                'Root.RFSoC.Application.SigGenLoader.Amplitude'    : f'{epics_prefix}:Root:RFSoC:Application:SigGenLoader:Amplitude',
                'Root.RFSoC.Application.SigGenLoader.Decay'        : f'{epics_prefix}:Root:RFSoC:Application:SigGenLoader:Decay',
                'Root.RFSoC.Application.SigGenLoader.Rise'         : f'{epics_prefix}:Root:RFSoC:Application:SigGenLoader:Rise',
                'Root.RFSoC.Application.SigGenLoader.IncidentTime' : f'{epics_prefix}:Root:RFSoC:Application:SigGenLoader:IncidentTime',

                # Waveform Ring Buffer variables
                'Root.PvAdc[0].Updated'      : f'{epics_prefix}:Root:PvAdc[0]:Updated',
                'Root.PvAdc[0].Time'         : f'{epics_prefix}:Root:PvAdc[0]:Time',
                'Root.PvAdc[0].WaveformData' : f'{epics_prefix}:Root:PvAdc[0]:WaveformData',
                'Root.PvDac[0].Updated'      : f'{epics_prefix}:Root:PvDac[0]:Updated',
                'Root.PvDac[0].Time'         : f'{epics_prefix}:Root:PvDac[0]:Time',
                'Root.PvDac[0].WaveformData' : f'{epics_prefix}:Root:PvDac[0]:WaveformData',
            }

            self.epics = pyrogue.protocols.epicsV4.EpicsPvServer(
                base      = self.epics_prefix,
                root      = self,
                pvMap     = self.pv_map,
                incGroups = None,
                excGroups = None,
            )
            self.addProtocol(self.epics)

        ##################################################################################

    def start(self,**kwargs):
        super(Root, self).start(**kwargs)

        # Update all SW remote registers
        self.ReadAll()

        # Load the Default YAML file
        print(f'Loading path={self.defaultFile} Default Configuration File...')
        self.LoadConfig(self.defaultFile)
        self.ReadAll()

        # Initialize the LMK/LMX Clock chips
        self.Hardware.InitClock(lmkConfig=self.lmkConfig,lmxConfig=[self.lmxConfig])

        # Initialize the RF Data Converter
        self.RFSoC.RfDataConverter.Init()

        # Wait for DSP Clock to be stable
        while(self.RFSoC.AxiSocCore.AxiVersion.DspReset.get()):
            time.sleep(0.01)

        # Load the waveform
        self.RFSoC.Application.SigGenLoader.LoadWaveform()

        # Update all SW remote registers
        self.ReadAll()

    ##################################################################################
