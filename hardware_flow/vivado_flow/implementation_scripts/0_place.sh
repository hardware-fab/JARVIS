################################################
# Authors  :   Andrea Galimberti (andrea.galimberti@polimi.it),
#              Davide Galli (davide.galli@polimi.it),
#              Davide Zoni (davide.zoni@polimi.it)
################################################

#cmdLine ./0_place.sh [--xilinx_checkpoint <file>] [--fpga-part <part>] [--target-top-name <name>]

# Default values
TARGET_TOP_NAME="jarvisTop"
XILINX_CHECKPOINT="../synthesize_chekpoints/${TARGET_TOP_NAME}_synth_checkpoint.dcp"
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

echo "" > target_place.tcl
echo "############################################################"
echo "##                 PLACE: starting task ...               ##"
echo "############################################################"
#
# generate tcl script to execute
#
echo "open_checkpoint -part ${FPGA_PART} ${XILINX_CHECKPOINT}" >> target_place.tcl
echo "" >> target_place.tcl
echo "place_design" >> target_place.tcl
echo "phys_opt_design" >> target_place.tcl
#echo "phys_opt_design -directive ExploreWithHoldFix" >> target_place.tcl
echo "report_timing_summary -file ./timing_place.txt" >> target_place.tcl
echo "write_checkpoint ./${TARGET_TOP_NAME}_place_checkpoint -force" >> target_place.tcl
echo "quit" >> target_place.tcl
#
# execute the PLACE task
#
vivado -mode tcl -source target_place.tcl

echo "############################################################"
echo "##                 PLACE: completed                       ##"
echo "############################################################"
