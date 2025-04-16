# JARVIS on FPGA using Vivado

This directory leverages the _AMD Xilinx Vivado_ tool to implement the JARVIS platform on FPGA targets.

## Organization

The directory is organized as follows:

- `/hdl_src`: Contains the source files for the JARVIS platform, including testbench and XDC constraints.
  - `\netlist`: Contains Verilog netlists for the SoC with a flatten hierarchy.

  - `\tb`: Includes the testbench for verification.
  - `\xdc`: Provides XDC constraints for the target FPGA.
- `/vivado_flow`: Contains scripts for implementation and bitstream generation using Vivado.

```txt
.
├── hdl_src
│   ├── netlist
│   │   ├── jarvisTop_synth_simulation.v
│   │   └── jarvisTop_synth.v
│   ├── tb
│   │   └── tb_jarvisSCA.sv
│   └── xdc
│       ├── all_board_timing.xdc
│       ├── all_board_trng.xdc
│       └── board_CW305.xdc
└── vivado_flow
    ├── implementation_scripts
    │   ├── 0_place.sh
    │   ├── 1_route.sh
    │   ├── 2_bitstream.sh
    │   └── clean.sh
    ├── synthesize_chekpoints
    │   └── jarvisTop_synth_checkpoint.dcp
    └── synth_impl_bitstream.sh
```

### Netlist Overview

This project includes two distinct netlists, each tailored for specific use cases:

1. **Simulation Netlist** (`jarvisTop_synth_simulation.v`):
    - Designed for simulation purposes.
    - Replaces the True Random Number Generator (TRNG) with a fake TRNG to accelerate simulation.
    - Features a bus as the top-level port to enable faster binary loading during simulation.

2. **Implementation Netlist** (`jarvisTop_synth.v`):
    - Intended for real-world implementation.
    - Incorporates a real TRNG for authentic randomness.
    - Utilizes a UART interface for binary loading, ensuring compatibility with hardware constraints.

These configurations allow for efficient testing and deployment by addressing the unique requirements of simulation and implementation environments.

## Using Vivado flow

To simulate, synthetize and implement the SoC, we recommend to use AMD Xilinx Vivado.

### Prerequisites

To install the tool for your platorm, follow the official [website](https://www.xilinx.com/support/download.html).

### Synthetize and implement

To run the complete flow and generate the bitstream:

```bash
cd vivado_flow
./impl_bitstream.sh [--board-xdc-file <file>] [--fpga-part <part>] [--target-top-name <name>]
```

| Parameter             | Shortcut  | Description                                      | Default          |
|---------------------- |-----------|--------------------------------------------------|------------------|
| --board-xdc-file      | -xdc      | XDC file for the target board                    | board_CW305.xdc  |
| --fpga-part           | -fpga     | FPGA part number                                 | xc7a100tftg256-1 |
| --target-top-name     | -top      | Name of the top-level design entity              | jarvisTop          |

As output you will find a `jarvisTop.bit` file for flashing the target FPGA.

## Note

The hdl code has been tested with AMD Xilinx Vivado 2022.1.
