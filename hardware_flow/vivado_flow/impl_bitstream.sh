################################################
# Authors  :   Andrea Galimberti (andrea.galimberti@polimi.it),
#              Davide Galli (davide.galli@polimi.it),
#              Davide Zoni (davide.zoni@polimi.it)
################################################

#!/bin/bash

# Default values
BOARD_XDC_FILE="board_CW305.xdc"
FPGA_PART="xc7a100tftg256-1"
TARGET_TOP_NAME="jarvisTop"

# Parse cmd
while (( "$#" )); do
  case "$1" in
    -h)
      echo "Use: $0 [--board-xdc-file <file>] [--fpga-part <part>] [--target-top-name <name>]"
      exit 0
      ;;
    -xdc | --board-xdc-file)
      BOARD_XDC_FILE="$2"
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
echo "  board_xdc_file: $BOARD_XDC_FILE"
echo "  fpga_part: $FPGA_PART"
echo "  target_top_name: $TARGET_TOP_NAME"
echo ""

cd ../implementation_scripts
./0_place.sh -fpga $FPGA_PART -top $TARGET_TOP_NAME
./1_route.sh -fpga $FPGA_PART -top $TARGET_TOP_NAME
./2_bitstream.sh -fpga $FPGA_PART -top $TARGET_TOP_NAME
./clean.sh