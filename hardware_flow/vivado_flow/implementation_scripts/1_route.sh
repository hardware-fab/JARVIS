################################################
# Authors  :   Andrea Galimberti (andrea.galimberti@polimi.it),
#              Davide Galli (davide.galli@polimi.it),
#              Davide Zoni (davide.zoni@polimi.it)
################################################

#cmdLine ./1_route.sh [--xilinx_checkpoint <file>] [--fpga-part <part>] [--target-top-name <name>]

# Default values
TARGET_TOP_NAME="jarvisTop"
XILINX_CHECKPOINT="./${TARGET_TOP_NAME}_place_checkpoint.dcp"
FPGA_PART="xc7a100tftg256-1"

# Parse cmd
while (( "$#" )); do
  case "$1" in
    -h)
      echo "Use: $0 [--xilinx_checkpoint <file>] [--fpga-part <part>] [--target-top-name <name>]"
      exit 0
      ;;
    -ckp | --xilinx_checkpoint)
      XILINX_CHECKPOINT="$2"
      shift 2
      ;;
    -fpga | --fpga-part)
      FPGA_PART="$2"
      shift 2
      ;;
    -top | --target-top-name)
      TARGET_TOP_NAME="$2"
      shift 2
      ;;
    --) # end argument parsing
      shift
      break
      ;;
    -*|--*=) # unsupported flags
      echo "Error: unsupported flag $1" >&2
      exit 1
      ;;
    *) # preserve positional arguments
      PARAMS="$PARAMS $1"
      shift
      ;;
  esac
done

# set positional arguments in their proper place
eval set -- "$PARAMS"

# print values
echo "Configuration:"
echo "  xilinx_checkpoint: $XILINX_CHECKPOINT"
echo "  fpga_part: $FPGA_PART"
echo "  target_top_name: $TARGET_TOP_NAME"
echo ""

echo "" > target_route.tcl
echo "############################################################"
echo "##                ROUTE: starting task ...                ##"
echo "############################################################"
#
# generate tcl script to execute
#
echo "open_checkpoint -part ${FPGA_PART} ${XILINX_CHECKPOINT}" >> target_route.tcl
echo "route_design -directive Explore" >> target_route.tcl
echo "phys_opt_design" >> target_route.tcl
#echo "phys_opt_design -directive Explore" >> target_route.tcl 
#echo "phys_opt_design -clock_opt" >> target_route.tcl 
#echo "phys_opt_design -directive ExploreWithHoldFix" >> target_place.tcl
echo "report_timing_summary -file ./timing_route.txt" >> target_route.tcl
echo "write_checkpoint -force ./${TARGET_TOP_NAME}_route_checkpoint" >> target_route.tcl
#echo "write_verilog -force ./${TARGET_TOP_NAME}_impl.v -mode timesim -write_all_overrides -sdf_anno true -sdf_file ./${TARGET_TOP_NAME}_impl.sdf -include_xilinx_libs" >> target_route.tcl
echo "write_verilog -force ./${TARGET_TOP_NAME}_impl.v -mode timesim -write_all_overrides -sdf_anno true -sdf_file ./${TARGET_TOP_NAME}_impl.sdf" >> target_route.tcl
echo "write_sdf -process_corner slow -force ./${TARGET_TOP_NAME}_impl.sdf -mode timesim" >> target_route.tcl
#echo "write_sdf -process_corner fast -force ./${TARGET_TOP_NAME}_impl.sdf -mode timesim" >> target_route.tcl
echo "quit" >> target_route.tcl
#
# execute the ROUTE task
#
vivado -mode tcl -source target_route.tcl

echo "############################################################"
echo "##                 ROUTE: completed                       ##"
echo "############################################################"
