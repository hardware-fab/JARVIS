// *************************************************
// Authors :   Andrea Galimberti (andrea.galimberti@polimi.it),
//             Davide Galli (davide.galli@polimi.it),
//             Davide Zoni (davide.zoni@polimi.it)
//
// *************************************************

#ifndef TRNG_H
#define TRNG_H

#define TRNG_ADDRESS 0x400000

#define TRNG() ({ \
    uint32_t rng; \
    __asm__ volatile ( \
        "lw %0, 0(%1)" \
        : "=r" (rng) \
        : "rm" (TRNG_ADDRESS) \
    ); \
    rng; \
})

#endif