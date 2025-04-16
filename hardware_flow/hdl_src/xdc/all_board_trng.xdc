#################
# NLFIRO        #
#################
set_false_path -through [get_pins -hierarchical -regexp .*nlfiro/rnd_o]
set_property ALLOW_COMBINATORIAL_LOOPS true [get_nets -hierarchical -regexp .*fibonacci]

#################
# ES #
#################
#set_property ALLOW_COMBINATORIAL_LOOPS TRUE [get_nets -hierarchical -regexp .*ro1_out]
#set_property ALLOW_COMBINATORIAL_LOOPS TRUE [get_nets -hierarchical -regexp .*ro2_out]
#set_false_path -through [get_pins -hierarchical -regexp .*ro2_nand/O]

#################
# TRNG PLL #
#################
#set_false_path -from [get_clocks clk_0]
#set_false_path -to [get_clocks clk_0]

