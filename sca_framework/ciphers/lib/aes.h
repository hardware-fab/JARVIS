// *********************************************
// Authors  : 	Andrea Galimberti (andrea.galimberti@polimi.it),
//              Davide Galli (davide.galli@polimi.it),
//              Davide Zoni (davide.zoni@polimi.it)
// *********************************************

#include <stdint.h>

uint8_t KeyExpansion(uint8_t fullkeys[11][16], uint8_t* key);
void AES_in_place(uint8_t k[11][16], uint8_t* m);