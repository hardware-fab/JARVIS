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

For more details, please see the preprint of our [Transactions on Computers article](https://arxiv.org/abs/2407.17432):
```bibtex
@misc{Zoni_2024TC-JARVIS-arXiv,
      title={An FPGA-Based Open-Source Hardware-Software Framework for Side-Channel Security Research}, 
      author={Davide Zoni and Andrea Galimberti and Davide Galli},
      year={2024},
      eprint={2407.17432},
      archivePrefix={arXiv},
      primaryClass={cs.CR},
      url={https://arxiv.org/abs/2407.17432}, 
}
```
