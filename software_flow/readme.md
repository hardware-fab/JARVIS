# Software Flow

This framework leverages the _RISC-V GNU Compiler Toolchain_ and _FreeRTOS_  with custom modifications to compile C files the JARVIS platform.

## Organization

The directory is organized as follows:

- `/bench`: Contains C implementations of ciphers adapted for the JARVIS platform, including masked and morphed versions of the AES cipher.
These ciphers are derived from the [OpenSSL repostory](https://github.com/openssl/openssl).
- `/compile_scripts`: Contains several scripts to compile benchmarks and the RTOS for RISC-V and JARVIS.
- `/drivers`: Contains C code for JARVIS drivers.
- `/low_level`: Contains linker and initialization files.
- `/RTOS`: Contains a modify Real Time Operatin System (RTOS)
with a demonstration of the chaffing countermeasure.

```txt
.
├── bench
│   ├── out/
│   ├── aes.c
│   ├── aes_masked.c
│   ├── aes_morphed.c
│   ├── aes_RTOS.c
│   ├── camellia.c
│   ├── clefia.c
│   ├── seed.c
│   ├── trng.c
│   └── trng.h
├── compile_scripts
│   ├── utils/
│   ├── clean_RTOS.sh
│   ├── compile_bench.sh
│   ├── compile_demo_RTOS.sh
│   └── vmem_formatter
├── drivers/
├── low_level/
└── RTOS
    ├── demo
    │   ├── chaffing
    │   │   ├── chaff_aes.c
    │   │   ├── FreeRTOSConfig.h
    │   │   ├── main.c
    │   │   ├── Makefile
    │   │   ├── random_scheduler.h
    │   │   ├── riscv-reg.h
    │   │   ├── riscv-virt.c
    │   │   ├── riscv-virt.h
    │   │   ├── start.S
    │   │   └── vector.S
    │   └── out/
    ├── FreeRTOS-Kernel/
    ├── build.sh
    └── random_scheduler.patch
```

## Installation

### Prerequisites

Install RISC-V GNU Compiler Toolchain.

1. Clone the repository:

    ```bash
    git clone https://github.com/riscv-collab/riscv-gnu-toolchain.git
    ```

2. Install dependencies:

    ```bash
    sudo apt-get install autoconf automake autotools-dev curl python3 python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev
    ```

3. Configure and install the toolchain:

    ```bash
    cd riscv-gnu-toolchain
    ./configure --prefix=</path/to/install> --with-arch=rv32imf --with-abi=ilp32f
    make
    ```

    Replace `</path/to/install>` with the desired writable installation path (e.g., /opt/riscv).

4. Add `bin` directory in the installation path to your `PATH`.

Refer to the RISC-V GNU toolchain [README](https://github.com/riscv-collab/riscv-gnu-toolchain) for detailed installation instructions.

### RTOS

As Real Time Operatin System we chose [FreeRTOS](https://www.freertos.org/index.html) V11.0.1.  
To clone the FreeRTOS repository and patch it with the costum random scheduler, run these commands:

```bash
cd RTOS
chmod +x build.sh
./build.sh
```

## Compilation flow

Navigate to the `compile_scripts` directory before running any compilation scripts.

- Compile a benchmark for RISC-V:

    ```bash
    ./compile_bench.sh <src_file>
    ```

    Replace `<src_file>` with the desired benchmark file (e.g. aes).

- Compile the chaffing RTOS demo for RISC-V:

    ```bash
    ./compile_demo_RTOS.sh
    ```

As output of the compilation flow you will find two files: a `.vmem` file to load into JARVIS memory and a `.objdump` with the disassembled code for debugging.

## Note

- Cipher implementations are based on the OpenSSL [repository](https://github.com/openssl/openssl).  
- Masked AES is derived from the MELITY [project](https://github.com/CENSUS/masked-aes-c).
