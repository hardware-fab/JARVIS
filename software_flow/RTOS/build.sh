################################################
# Authors  :   Andrea Galimberti (andrea.galimberti@polimi.it),
#              Davide Galli (davide.galli@polimi.it),
#              Davide Zoni (davide.zoni@polimi.it)
################################################

#!/bin/bash

# Clone the repository
git clone --branch V11.0.1 https://github.com/FreeRTOS/FreeRTOS-Kernel.git

# Apply patch for random scheduler
cd FreeRTOS-Kernel
patch -p1 < ../random_scheduler.patch
cd ..
