# JARVIS

**JARVIS** (**J**ust **A** **R**ISC-**V** **I**nfrastructure for **S**CA) is a research framework for side-channel analysis (SCA) on FPGA-based IoT-class computing platforms.

The JARVIS framework provides an IoT-class system-on-chip (SoC) that includes:

- CPU based on the RISC-V ISA,
- dedicated hardware to enable the implementation of state-of-the-art SCA countermeasures,
- ad-hoc debug infrastructure to maximize the observability and controllability of the computing platform and simplify the execution of SCA attacks,
- support for the open-source FreeRTOS real-time operating system.

A complete hardware-software flow encompasses:

1. configuration of the RISC-V-based SoC,
2. execution of the target applications and corresponding collection of side-channel information,
3. analysis to identify SCA vulnerabilities and leakage sources.

For more details, please see our [Transactions on Computers article](https://ieeexplore.ieee.org/document/10929027).

## Organization

The repository is organized as follows:

- `/hardware_flow`: Contains the verilog files for the JARVIS implementation and the scripts to implement it on FPGA.
- `/sca_framework`: Contains the Python side-channel analysis framework, encompassing scripts and notebooks for implementing various attack types.
- `/software_flow`: Contains C implementations of ciphers with side-channel countermeausre, a modified FreeRTOS implementation with a random scheduler, and the script to compile for RISC-V.

```
.
├── hardware_flow
│   ├── config_DFS/
│   ├── hdl_src/
│   └── vivado_flow/
├── sca_framework
│   ├── attack/
│   ├── ciphers/
│   ├── io_dat/
│   ├── low_level/
│   ├── sca_utils/
│   ├── cpa_attack.ipynb
│   ├── collect_side-channel.ipynb
│   ├── cnn_attack.ipynb
│   ├── SNR.ipynb
│   └── template_attack.ipynb
└── software_flow
    ├── bench/
    ├── compile_scripts/
    ├── drivers/
    ├── low_level/
    └── RTOS/
        ├── build.sh
        ├── demo/
        └── random_scheduler.patch
```

## Installation

Refer to the individual `README.md` files within each subdirectory ([hardware_flow](https://github.com/hardware-fab/JARVIS/blob/main/hardware_flow/readme.md), [sca_framework](https://github.com/hardware-fab/JARVIS/blob/main/sca_framework/readme.md), and [software_flow](https://github.com/hardware-fab/JARVIS/blob/main/software_flow/readme.md)) for specific installation instruction.

## Note

This repository has been publish as part of [IEEE Transactions on Computers article](https://ieeexplore.ieee.org/document/10929027).  
A [preprint version](https://arxiv.org/abs/2407.17432) is also freely available online on arXiv.


```bibtex
@ARTICLE{Zoni_2025TC-JARVIS,
  author={Zoni, Davide and Galimberti, Andrea and Galli, Davide},
  journal={IEEE Transactions on Computers}, 
  title={An FPGA-Based Open-Source Hardware-Software Framework for Side-Channel Security Research}, 
  year={2025},
  pages={1-13},
  doi={10.1109/TC.2025.3551936}
}
```

This repository is protected by copyright and licensed under the [Apache-2.0 license](https://github.com/hardware-fab/JARVIS/blob/main/LICENSE) file.

© 2025 hardware-fab