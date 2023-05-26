-------------------------------------------------------------------------------
-- Company    : SLAC National Accelerator Laboratory
-------------------------------------------------------------------------------
-- Description: RfDataConverter Module
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

entity RfDataConverter is
   generic (
      TPD_G            : time := 1 ns;
      AXIL_BASE_ADDR_G : slv(31 downto 0));
   port (
      -- RF DATA CONVERTER Ports
      adcClkP         : in  slv(1 downto 0);
      adcClkN         : in  slv(1 downto 0);
      adcP            : in  slv(3 downto 0);
      adcN            : in  slv(3 downto 0);
      dacClkP         : in  slv(1 downto 0);
      dacClkN         : in  slv(1 downto 0);
      dacP            : out slv(1 downto 0);
      dacN            : out slv(1 downto 0);
      sysRefP         : in  sl;
      sysRefN         : in  sl;
      -- ADC/DAC Interface (dspClk domain)
      dspClk          : out sl;
      dspRst          : out sl;
      dspAdc          : out slv(63 downto 0);
      dspDac          : in  slv(255 downto 0);
      -- AXI-Lite Interface (axilClk domain)
      axilClk         : in  sl;
      axilRst         : in  sl;
      axilWriteMaster : in  AxiLiteWriteMasterType;
      axilWriteSlave  : out AxiLiteWriteSlaveType;
      axilReadMaster  : in  AxiLiteReadMasterType;
      axilReadSlave   : out AxiLiteReadSlaveType);
end RfDataConverter;

architecture mapping of RfDataConverter is

   component RfDataConverterIpCore
      port (
         adc2_clk_p      : in  std_logic;
         adc2_clk_n      : in  std_logic;
         clk_adc2        : out std_logic;
         dac2_clk_p      : in  std_logic;
         dac2_clk_n      : in  std_logic;
         clk_dac2        : out std_logic;
         s_axi_aclk      : in  std_logic;
         s_axi_aresetn   : in  std_logic;
         s_axi_awaddr    : in  std_logic_vector(17 downto 0);
         s_axi_awvalid   : in  std_logic;
         s_axi_awready   : out std_logic;
         s_axi_wdata     : in  std_logic_vector(31 downto 0);
         s_axi_wstrb     : in  std_logic_vector(3 downto 0);
         s_axi_wvalid    : in  std_logic;
         s_axi_wready    : out std_logic;
         s_axi_bresp     : out std_logic_vector(1 downto 0);
         s_axi_bvalid    : out std_logic;
         s_axi_bready    : in  std_logic;
         s_axi_araddr    : in  std_logic_vector(17 downto 0);
         s_axi_arvalid   : in  std_logic;
         s_axi_arready   : out std_logic;
         s_axi_rdata     : out std_logic_vector(31 downto 0);
         s_axi_rresp     : out std_logic_vector(1 downto 0);
         s_axi_rvalid    : out std_logic;
         s_axi_rready    : in  std_logic;
         irq             : out std_logic;
         sysref_in_p     : in  std_logic;
         sysref_in_n     : in  std_logic;
         vin2_23_p       : in  std_logic;
         vin2_23_n       : in  std_logic;
         vout20_p        : out std_logic;
         vout20_n        : out std_logic;
         m2_axis_aresetn : in  std_logic;
         m2_axis_aclk    : in  std_logic;
         m22_axis_tdata  : out std_logic_vector(63 downto 0);
         m22_axis_tvalid : out std_logic;
         m22_axis_tready : in  std_logic;
         s2_axis_aresetn : in  std_logic;
         s2_axis_aclk    : in  std_logic;
         s20_axis_tdata  : in  std_logic_vector(255 downto 0);
         s20_axis_tvalid : in  std_logic;
         s20_axis_tready : out std_logic
         );
   end component;

   signal refClk   : sl := '0';
   signal axilRstL : sl := '0';

   signal dspClk508  : sl := '0';
   signal dspRst508  : sl := '1';
   signal dspRst508L : sl := '0';

begin

   U_IpCore : RfDataConverterIpCore
      port map (
         -- Clock Ports
         adc2_clk_p      => adcClkP(1),
         adc2_clk_n      => adcClkN(1),
         clk_adc2        => open,
         dac2_clk_p      => dacClkP(1),
         dac2_clk_n      => dacClkN(1),
         clk_dac2        => refClk,
         -- AXI-Lite Ports
         s_axi_aclk      => axilClk,
         s_axi_aresetn   => axilRstL,
         s_axi_awaddr    => axilWriteMaster.awaddr(17 downto 0),
         s_axi_awvalid   => axilWriteMaster.awvalid,
         s_axi_awready   => axilWriteSlave.awready,
         s_axi_wdata     => axilWriteMaster.wdata,
         s_axi_wstrb     => axilWriteMaster.wstrb,
         s_axi_wvalid    => axilWriteMaster.wvalid,
         s_axi_wready    => axilWriteSlave.wready,
         s_axi_bresp     => axilWriteSlave.bresp,
         s_axi_bvalid    => axilWriteSlave.bvalid,
         s_axi_bready    => axilWriteMaster.bready,
         s_axi_araddr    => axilReadMaster.araddr(17 downto 0),
         s_axi_arvalid   => axilReadMaster.arvalid,
         s_axi_arready   => axilReadSlave.arready,
         s_axi_rdata     => axilReadSlave.rdata,
         s_axi_rresp     => axilReadSlave.rresp,
         s_axi_rvalid    => axilReadSlave.rvalid,
         s_axi_rready    => axilReadMaster.rready,
         -- Misc. Ports
         irq             => open,
         sysref_in_p     => sysRefP,
         sysref_in_n     => sysRefN,
         -- ADC Ports
         vin2_23_p       => adcP(3),
         vin2_23_n       => adcN(3),
         -- DAC Ports
         vout20_p        => dacP(1),
         vout20_n        => dacN(1),
         -- ADC AXI Stream Interface
         m2_axis_aresetn => dspRst508L,
         m2_axis_aclk    => dspClk508,
         m22_axis_tdata  => dspAdc,
         m22_axis_tvalid => open,
         m22_axis_tready => '1',
         -- DAC AXI Stream Interface
         s2_axis_aresetn => dspRst508L,
         s2_axis_aclk    => dspClk508,
         s20_axis_tdata  => dspDac,
         s20_axis_tvalid => '1',
         s20_axis_tready => open);

   U_Pll : entity surf.ClockManagerUltraScale
      generic map(
         TPD_G             => TPD_G,
         TYPE_G            => "PLL",
         INPUT_BUFG_G      => false,
         FB_BUFG_G         => true,
         RST_IN_POLARITY_G => '1',
         NUM_CLOCKS_G      => 1,
         -- MMCM attributes
         CLKIN_PERIOD_G    => 1.968,    -- 508 MHz
         CLKFBOUT_MULT_G   => 2,        -- 1016 MHz = 2 x 508 MHz
         CLKOUT0_DIVIDE_G  => 2)        -- 508 MHz = 1016 MHz / 2
      port map(
         -- Clock Input
         clkIn     => refClk,
         rstIn     => axilRst,
         -- Clock Outputs
         clkOut(0) => dspClk508,
         -- Reset Outputs
         rstOut(0) => dspRst508);

   U_axilRstL : entity surf.RstPipeline
      generic map(
         TPD_G     => TPD_G,
         INV_RST_G => true)             -- Invert RESET
      port map(
         clk    => axilClk,
         rstIn  => axilRst,
         rstOut => axilRstL);

   U_dspRst508L : entity surf.RstPipeline
      generic map(
         TPD_G     => TPD_G,
         INV_RST_G => true)             -- Invert RESET
      port map(
         clk    => dspClk508,
         rstIn  => dspRst508,
         rstOut => dspRst508L);

   dspClk <= dspClk508;
   U_dspRst : entity surf.RstPipeline
      generic map(
         TPD_G => TPD_G)
      port map(
         clk    => dspClk508,
         rstIn  => dspRst508,
         rstOut => dspRst);

end mapping;
