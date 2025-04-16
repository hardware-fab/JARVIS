## CW305

# Clock signal
set_property -dict {PACKAGE_PIN N13 IOSTANDARD LVCMOS33} [get_ports CLK_PIN]
create_clock -period 10.000 -name sys_clk_pin -waveform {0.000 5.000} -add [get_ports CLK_PIN]

# Negative reset
set_property -dict {PACKAGE_PIN R1 IOSTANDARD LVCMOS33} [get_ports NRST_PIN]

## GPIO
set_property -dict {PACKAGE_PIN A12 IOSTANDARD LVCMOS33} [get_ports sysUartRx]
set_property -dict {PACKAGE_PIN B12 IOSTANDARD LVCMOS33} [get_ports sysUartTx]

set_property -dict { PACKAGE_PIN A14   IOSTANDARD LVCMOS33 } [get_ports { usrUartRx }];        #IO_L5N_T0_AD9N_15
set_property -dict { PACKAGE_PIN A13   IOSTANDARD LVCMOS33 } [get_ports { usrUartTx }];        #IO_L5P_T0_AD9P_15

set_property -dict {PACKAGE_PIN A14 IOSTANDARD LVCMOS33} [get_ports TRIGGER_PIN_0]

# RED LED
#set_property -dict {PACKAGE_PIN T2 IOSTANDARD LVCMOS33} [get_ports {led[0]}]

# GREEN LED
#set_property -dict {PACKAGE_PIN T3 IOSTANDARD LVCMOS33} [get_ports {led[1]}]

# BLUE LED
#set_property -dict {PACKAGE_PIN T4 IOSTANDARD LVCMOS33} [get_ports {led[2]}]
