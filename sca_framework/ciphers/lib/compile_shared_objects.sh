#!/bin/bash

# Compile shared object in each subdirectory
gcc -shared -o aes.so -fPIC aes.c