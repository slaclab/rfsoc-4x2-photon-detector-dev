-------------------------------------------------------------------------------
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: Application Module
-------------------------------------------------------------------------------
-- This file is part of 'rfsoc-4x2-photon-detector-dev'.
-- It is subject to the license terms in the LICENSE.txt file found in the
-- top-level directory of this distribution and at:
--    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
-- No part of 'rfsoc-4x2-photon-detector-dev', including this file,
-- may be copied, modified, propagated, or distributed except according to
-- the terms contained in the LICENSE.txt file.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library surf;
use surf.StdRtlPkg.all;
use surf.AxiStreamPkg.all;
use surf.AxiLitePkg.all;
use surf.SsiPkg.all;

library work;
use work.AppPkg.all;

library axi_soc_ultra_plus_core;
use axi_soc_ultra_plus_core.AxiSocUltraPlusPkg.all;

entity Application is
   generic (
      TPD_G            : time := 1 ns;
      AXIL_BASE_ADDR_G : slv(31 downto 0));
   port (
      -- DMA Interface (dmaClk domain)
      dmaClk          : in  sl;
      dmaRst          : in  sl;
      dmaIbMasters    : out AxiStreamMasterArray(1 downto 0);
      dmaIbSlaves     : in  AxiStreamSlaveArray(1 downto 0);
      -- ADC/DAC Interface (dspClk domain)
      dspClk          : in  sl;
      dspRst          : in  sl;
      dspAdc          : in  slv(63 downto 0);
      dspDac          : out slv(255 downto 0);
      -- AXI-Lite Interface (axilClk domain)
      axilClk         : in  sl;
      axilRst         : in  sl;
      axilWriteMaster : in  AxiLiteWriteMasterType;
      axilWriteSlave  : out AxiLiteWriteSlaveType;
      axilReadMaster  : in  AxiLiteReadMasterType;
      axilReadSlave   : out AxiLiteReadSlaveType);
end Application;

architecture mapping of Application is

   constant RING_INDEX_C       : natural := 0;
   constant DAC_SIG_INDEX_C    : natural := 1;
   constant DEBUG_INDEX_C      : natural := 2;
   constant NUM_AXIL_MASTERS_C : natural := 3;

   constant AXIL_CONFIG_C : AxiLiteCrossbarMasterConfigArray(NUM_AXIL_MASTERS_C-1 downto 0) := genAxiLiteConfig(NUM_AXIL_MASTERS_C, AXIL_BASE_ADDR_G, 28, 24);

   signal axilReadMasters  : AxiLiteReadMasterArray(NUM_AXIL_MASTERS_C-1 downto 0);
   signal axilReadSlaves   : AxiLiteReadSlaveArray(NUM_AXIL_MASTERS_C-1 downto 0)  := (others => AXI_LITE_READ_SLAVE_EMPTY_DECERR_C);
   signal axilWriteMasters : AxiLiteWriteMasterArray(NUM_AXIL_MASTERS_C-1 downto 0);
   signal axilWriteSlaves  : AxiLiteWriteSlaveArray(NUM_AXIL_MASTERS_C-1 downto 0) := (others => AXI_LITE_WRITE_SLAVE_EMPTY_DECERR_C);

   signal adc : slv(63 downto 0)  := (others => '0');
   signal dac : slv(255 downto 0) := (others => '0');

   signal startDacStrb : sl;

   signal writeReg : slv(31 downto 0) := (others => '0');
   signal readReg  : slv(31 downto 0) := (others => '0');

begin

   process(dspClk)
   begin
      -- Help with making timing
      if rising_edge(dspClk) then
         adc    <= dspAdc after TPD_G;
         dspDac <= dac    after TPD_G;
      end if;
   end process;

   U_XBAR : entity surf.AxiLiteCrossbar
      generic map (
         TPD_G              => TPD_G,
         NUM_SLAVE_SLOTS_G  => 1,
         NUM_MASTER_SLOTS_G => NUM_AXIL_MASTERS_C,
         MASTERS_CONFIG_G   => AXIL_CONFIG_C)
      port map (
         axiClk              => axilClk,
         axiClkRst           => axilRst,
         sAxiWriteMasters(0) => axilWriteMaster,
         sAxiWriteSlaves(0)  => axilWriteSlave,
         sAxiReadMasters(0)  => axilReadMaster,
         sAxiReadSlaves(0)   => axilReadSlave,
         mAxiWriteMasters    => axilWriteMasters,
         mAxiWriteSlaves     => axilWriteSlaves,
         mAxiReadMasters     => axilReadMasters,
         mAxiReadSlaves      => axilReadSlaves);

   U_AppRingBuffer : entity axi_soc_ultra_plus_core.AppRingBuffer
      generic map (
         TPD_G                  => TPD_G,
         EN_ADC_BUFF_G          => true,
         EN_DAC_BUFF_G          => true,
         NUM_ADC_CH_G           => 1,
         NUM_DAC_CH_G           => 1,
         ADC_SAMPLE_PER_CYCLE_G => 4,
         DAC_SAMPLE_PER_CYCLE_G => 16,
         RAM_ADDR_WIDTH_G       => 9,
         AXIL_BASE_ADDR_G       => AXIL_CONFIG_C(RING_INDEX_C).baseAddr)
      port map (
         -- DMA Interface (dmaClk domain)
         dmaClk          => dmaClk,
         dmaRst          => dmaRst,
         dmaIbMaster     => dmaIbMasters(0),
         dmaIbSlave      => dmaIbSlaves(0),
         -- ADC/DAC Interface (dspClk domain)
         dspClk          => dspClk,
         dspRst          => dspRst,
         dspAdc0         => adc,
         dspDac0         => dac,
         extTrigIn       => startDacStrb,
         -- AXI-Lite Interface (axilClk domain)
         axilClk         => axilClk,
         axilRst         => axilRst,
         axilReadMaster  => axilReadMasters(RING_INDEX_C),
         axilReadSlave   => axilReadSlaves(RING_INDEX_C),
         axilWriteMaster => axilWriteMasters(RING_INDEX_C),
         axilWriteSlave  => axilWriteSlaves(RING_INDEX_C));

   U_DacSigGen : entity axi_soc_ultra_plus_core.SigGen
      generic map (
         TPD_G              => TPD_G,
         NUM_CH_G           => 1,
         SAMPLE_PER_CYCLE_G => 16,
         RAM_ADDR_WIDTH_G   => 9,
         AXIL_BASE_ADDR_G   => AXIL_CONFIG_C(DAC_SIG_INDEX_C).baseAddr)
      port map (
         -- DAC Interface (dspClk domain)
         dspClk          => dspClk,
         dspRst          => dspRst,
         dspDacOut0      => dac,
         extTrigIn       => startDacStrb,
         -- AXI-Lite Interface (axilClk domain)
         axilClk         => axilClk,
         axilRst         => axilRst,
         axilReadMaster  => axilReadMasters(DAC_SIG_INDEX_C),
         axilReadSlave   => axilReadSlaves(DAC_SIG_INDEX_C),
         axilWriteMaster => axilWriteMasters(DAC_SIG_INDEX_C),
         axilWriteSlave  => axilWriteSlaves(DAC_SIG_INDEX_C));

   U_AxiLiteRegs : entity surf.AxiLiteRegs
      generic map (
         TPD_G           => TPD_G,
         NUM_WRITE_REG_G => 1,
         NUM_READ_REG_G  => 1)
      port map (
         -- AXI-Lite Bus
         axiClk           => axilClk,
         axiClkRst        => axilRst,
         axiReadMaster    => axilReadMasters(DEBUG_INDEX_C),
         axiReadSlave     => axilReadSlaves(DEBUG_INDEX_C),
         axiWriteMaster   => axilWriteMasters(DEBUG_INDEX_C),
         axiWriteSlave    => axilWriteSlaves(DEBUG_INDEX_C),
         -- User Read/Write registers
         writeRegister(0) => writeReg,
         readRegister(0)  => readReg);

   U_startDacStrb : entity surf.SynchronizerOneShot
      generic map(
         TPD_G => TPD_G)
      port map(
         clk     => dspClk,
         dataIn  => writeReg(0),
         dataOut => startDacStrb);

   -- Place holder for future processing
   dmaIbMasters(1) <= AXI_STREAM_MASTER_INIT_C;

end mapping;
