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

import numpy as np
import click

class SigGenLoader(pr.Device):
    def __init__(self,
            DacSigGen    = None,
            maxEvents    = 4,  # Max number of signal event that can be loaded
            ramWidth     = 9, # Must match RAM_ADDR_WIDTH_G config
            smplPerCycle = 16, # Must match SAMPLE_PER_CYCLE_G config
            sampleRate   = 8.128E+9, # Units of Hz
        **kwargs):
        super().__init__(**kwargs)

        self._maxEvents    = maxEvents
        self._DacSigGen    = DacSigGen
        self._ramDepth     = 2**ramWidth
        self._bufferLength = smplPerCycle*2**ramWidth
        self._smplRate     = sampleRate
        self._timeBin      = (1.0/sampleRate)
        dependencies       = []

        self.add(pr.LocalVariable(
            name    = 'Amplitude',
            typeStr = 'Int16[np]',
            units   = 'Counts',
            value   = np.full(shape=maxEvents, fill_value=5000, dtype=np.int16, order='C'),
        ))

        self.add(pr.LocalVariable(
            name    = 'Decay',
            typeStr = 'Float[np]',
            units   = 'seconds',
            value   = np.full(shape=maxEvents, fill_value=100.0E-9, dtype=np.float32, order='C'),
        ))

        self.add(pr.LocalVariable(
            name    = 'Rise',
            typeStr = 'Float[np]',
            units   = 'seconds',
            value   = np.full(shape=maxEvents, fill_value=10.0E-9, dtype=np.float32, order='C'),
        ))

        self.add(pr.LocalVariable(
            name    = 'IncidentTime',
            typeStr = 'Float[np]',
            units   = 'seconds',
            value   = np.full(shape=maxEvents, fill_value=4.0E-6, dtype=np.float32, order='C'),
        ))

        # @self.command(hidden=True)
        @self.command()
        def LoadWaveform():

            # Zero out the array
            wavesform = np.zeros(shape=self._bufferLength, dtype=np.float32, order='C')

            # Loop through the photons
            for i in range(self._maxEvents):

                # Get photon signal's parameters
                A  = float(self.Amplitude.value(index=i))
                B  = self.Decay.value(index=i)
                C  = self.Rise.value(index=i)
                T0 = self.IncidentTime.value(index=i)

                # Loop through the DAC's RAM depth
                for x in range(self._bufferLength):

                    # Calculate the time and delta time
                    t = float(x)*self._timeBin
                    deltaT = t-T0

                    # Check if time greater than incident time
                    if (deltaT>0):
                        # Calculate the waveform with superposition
                        wavesform[x] += A*np.exp(-1.0*deltaT/B)*(1-np.exp(-1.0*deltaT/C))

                        # Check for overflow
                        if (wavesform[x] > 32767.0):
                            wavesform[x] = 32767.0

                        # Check for underflow
                        if (wavesform[x] < -32767.0):
                            wavesform[x] = -32767.0

            # Loop through the DAC's RAM depth
            for x in range(self._bufferLength):

                # Update only the shadow variable value (write performance reasons)
                self._DacSigGen.Waveform[0].set(value=int(wavesform[x]),index=x,write=False)

            # Push all shadow variables to hardware
            self._DacSigGen.Waveform[0].write()

            # Reset the FSM after loading the waveform
            self._DacSigGen.Reset()
