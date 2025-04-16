################################################
# Authors             : Andrea Galimberti (andrea.galimberti@polimi.it),
#                       Davide Galli (davide.galli@polimi.it),
#                       Davide Zoni (davide.zoni@polimi.it)
#
# Other contributor(s): Andrea Motta
################################################

#!/bin/bash
cd ../RTOS/demo/chaffing
make clean

cd ../out
BENCH_NAME="RTOSDemo"

rm ${BENCH_NAME}*