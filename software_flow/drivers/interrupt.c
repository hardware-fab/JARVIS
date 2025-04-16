// *********************************************
// Authors  : 	Andrea Galimberti (andrea.galimberti@polimi.it),
//              Davide Galli (davide.galli@polimi.it),
//              Davide Zoni (davide.zoni@polimi.it)
// *********************************************

#include "interrupt.h"

__attribute__((weak)) void int_default_handler(void)
{
    while (1)
        ;
}