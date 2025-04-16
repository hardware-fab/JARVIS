// *************************************************
// The source code has been adapted from the following repository:
// https://github.com/openssl/openssl
//
// Copyright 2006-2020 The OpenSSL Project Authors. All Rights Reserved.
// Licensed under the Apache License 2.0 (the "License").  You may not use
// this file except in compliance with the License.  You can obtain a copy
// in the file LICENSE in the source distribution or at
// https://www.openssl.org/source/license.html
// 
// Other contributor(s) :  Andrea Galimberti (andrea.galimberti@polimi.it),
//                         Davide Galli (davide.galli@polimi.it),
//                         Davide Zoni (davide.zoni@polimi.it)
// 
// *************************************************

#include <stdint.h>

// constant execution time (no if instructions)
#define IS_CONST_TIME 1

// #define ISA 0     // Enable simulation exit sequence for riscv-polimi core
// #define ISA 1     // Enable debug mode on X86 machines
#define ISA 2 // For prototype: no x86 nor RISC-V ad-hoc statements

#if ISA == 0
#include "sim_handler.h"
#endif

#if ISA == 1
#include <stdio.h>
#endif

#define BATCH_SIZE 2048

const uint8_t sbox[256] = {
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
    0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc,
    0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a,
    0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
    0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
    0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85,
    0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
    0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17,
    0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88,
    0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
    0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9,
    0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6,
    0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
    0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94,
    0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68,
    0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16};

uint8_t rcon[] = {
    0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
    0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a};

uint8_t gmul(uint8_t a, uint8_t b)
{
    uint8_t i = 0;
    uint8_t p = 0;
    uint8_t hi_bit;
#if IS_CONST_TIME == 1
    // additional var to avoid data-dependant if
    struct
    {
        signed int tVal : 1;
    } s;
    uint8_t modVal = 0;
#endif

    for (i = 0; i < 8; ++i)
    {
#if IS_CONST_TIME == 1
        s.tVal = b & 1; // is b[0] bit set?
        modVal = s.tVal;
        p = p ^ (a & modVal);
#else
        if ((b & 1) == 1)
            p = p ^ a;
#endif
        hi_bit = (a & 0x80);
        a <<= 1;

#if IS_CONST_TIME == 1
        s.tVal = (hi_bit >> 7) & 1; // is hi_bit[7] bit set?
        modVal = s.tVal;
        a = a ^ (0x1b & modVal);
#else
        if (hi_bit == 0x80)
            a = a ^ 0x1b;
#endif
        b >>= 1;
    }
    return p;
}

uint8_t MixColumns(uint8_t *state)
{
    uint8_t i = 0;
    uint8_t s0, s1, s2, s3;

    for (i = 0; i < 16; i += 4)
    {
        s0 = state[i];
        s1 = state[i + 1];
        s2 = state[i + 2];
        s3 = state[i + 3];

        state[i] = gmul(0x02, s0) ^ gmul(0x03, s1) ^ s2 ^ s3;
        state[i + 1] = s0 ^ gmul(0x02, s1) ^ gmul(0x03, s2) ^ s3;
        state[i + 2] = s0 ^ s1 ^ gmul(0x02, s2) ^ gmul(0x03, s3);
        state[i + 3] = gmul(0x03, s0) ^ s1 ^ s2 ^ gmul(0x02, s3);
    }

    return 0;
}

uint8_t SubBytes(uint8_t *state)
{
    uint8_t i = 0;

    for (i = 0; i < 16; ++i)
    {
        state[i] = sbox[state[i]];
    }

    return 0;
}

uint8_t ShiftRows(uint8_t *state)
{
    uint8_t i = 0;
    uint8_t s0, s1, s2, s3;

    for (i = 1; i < 4; ++i)
    {
        s0 = state[(i + (4 * i)) % 16];
        s1 = state[(i + (4 * i) + 4) % 16];
        s2 = state[(i + (4 * i) + 8) % 16];
        s3 = state[(i + (4 * i) + 12) % 16];

        state[i] = s0;
        state[i + 4] = s1;
        state[i + 8] = s2;
        state[i + 12] = s3;
    }

    return 0;
}

uint8_t AddRoundKey(uint8_t *state, uint8_t *key)
{
    uint8_t i = 0;

    for (i = 0; i < 16; ++i)
    {
        state[i] ^= key[i];
    }

    return 0;
}

uint8_t ScheduleCore(uint8_t *nextkey, uint8_t *subkey, uint8_t rconi)
{
    uint8_t temp[4];

    // copy over to temp (incl rotation)
    temp[0] = sbox[subkey[13]];
    temp[1] = sbox[subkey[14]];
    temp[2] = sbox[subkey[15]];
    temp[3] = sbox[subkey[12]];

    nextkey[0] = subkey[0] ^ temp[0] ^ rcon[rconi];
    nextkey[1] = subkey[1] ^ temp[1];
    nextkey[2] = subkey[2] ^ temp[2];
    nextkey[3] = subkey[3] ^ temp[3];

    nextkey[4] = subkey[4] ^ nextkey[0];
    nextkey[5] = subkey[5] ^ nextkey[1];
    nextkey[6] = subkey[6] ^ nextkey[2];
    nextkey[7] = subkey[7] ^ nextkey[3];
    nextkey[8] = subkey[8] ^ nextkey[4];
    nextkey[9] = subkey[9] ^ nextkey[5];
    nextkey[10] = subkey[10] ^ nextkey[6];
    nextkey[11] = subkey[11] ^ nextkey[7];
    nextkey[12] = subkey[12] ^ nextkey[8];
    nextkey[13] = subkey[13] ^ nextkey[9];
    nextkey[14] = subkey[14] ^ nextkey[10];
    nextkey[15] = subkey[15] ^ nextkey[11];

    return 0;
}

uint8_t KeyExpansion(uint8_t fullkeys[11][16], uint8_t *key)
{
    uint8_t i;

    for (i = 0; i < 16; ++i)
    {
        fullkeys[0][i] = key[i];
    }

    for (i = 0; i < 10; ++i)
    {
        ScheduleCore(fullkeys[i + 1], fullkeys[i], i + 1);
    }

    return 0;
}

void AES_in_place(uint8_t k[11][16], uint8_t *m)
{
    uint8_t i;
    AddRoundKey(m, k[0]);
    for (i = 0; i < 9; ++i)
    {
        SubBytes(m);
        ShiftRows(m);
        MixColumns(m);
        AddRoundKey(m, k[i + 1]);
    }

    SubBytes(m);
    ShiftRows(m);
    AddRoundKey(m, k[i + 1]);
}


unsigned char key[16] = {0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c};
uint8_t state[16] = {0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41};
int iterDelay = 0;

int main()
{
    int i;
#if ISA == 1
    int j;
#endif
    uint8_t fullkeys[11][16];

    // expand the key to subkeys
    KeyExpansion(fullkeys, key);

    /* Receive initial state and encrypt it BATCH_SIZE times */
    for (i = 0; i < BATCH_SIZE; i++)
    {
        __asm__(".RISE_TRG:");
        for (iterDelay = 0; iterDelay < 800; iterDelay++)
            ;
#if ISA == 1
        for (j = 0; j < 16; j++)
            printf("%02x", state[j]);
        printf(" -> ");
#endif

        AES_in_place(fullkeys, state);
        __asm__(".FALL_TRG:");
        for (iterDelay = 0; iterDelay < 10000; iterDelay++)
            ;

#if ISA == 1
        for (j = 0; j < 16; j++)
            printf("%02x", state[j]);
        printf("\n");
#endif
    }
}
