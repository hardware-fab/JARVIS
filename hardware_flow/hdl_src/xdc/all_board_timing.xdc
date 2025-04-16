# Rename clk
create_generated_clock -name clk_dcm_50MHz [get_pins dcm0/mmcme2_adv_inst/CLKOUT0]

# DFS constraints
set_clock_groups -logically_exclusive -group [get_clocks -of_objects [get_pins wbSoC0/dfs/dfs0/mmcm_0/mmcm_adv_inst/CLKOUT0]] -group [get_clocks -of_objects [get_pins wbSoC0/dfs/dfs0/mmcm_1/mmcm_adv_inst/CLKOUT0]]
