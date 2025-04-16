# Side-Channel Analysis Framework

This framework leverages the _chipwhisperer-305_ and _PicoScope ps5000a_ to conduct Side Channel Analysis (SCA) on FPGA targets.
The toolflow is designed for the general-purpose JARVIS platform.

## Organization

The directory is organized as follows:

- `/`: Contains Jupiter Notebooks for collecting side-channel signals and perform four SCA techniques.
- `attack/`: Contains implementation of four SCA techniques: CNN attack, Template Attack, Correlation Power Analysis, Signal-to-Noise Ratio.
   - `CNN/`: Contains modules and configuration files for a proper CNN attack. The CNN has been adapted from the ASCAD CNN_best [1].
- `ciphers/`: Contains the AES cipher implemetation in Python leaveraging a compiled C library.
- `io_dat/`: Contains classes and methods to write and read data from the acquisition setup.
- `low_level/`: Contains classes and methods for interfacing with JARVIS SoC and PicoScope.
- `sca_utils/`: Contains helper functions for a proper side channel analysis.

```txt
.
├── attack
│   ├── CNN
│   │   ├── attack.py
│   │   ├── configs/
│   │   ├── create_dataset.py
│   │   ├── datasets/
│   │   ├── models/
│   │   ├── modules/
│   │   ├── train.py
│   │   └── utils/
│   ├── Cpa.py
│   ├── Snr.py
│   └── TemplateAttack.py
├── ciphers
│   ├── aes.py
│   ├── aesSca.py
│   └── lib/
├── io_dat
│   ├── adc.py
│   ├── output_writer.py
│   └── traces_bin.py
├── low_level
│   ├── jarvis.py
│   ├── picoscope.py
│   ├── riscv.py
│   └── uart.py
├── sca_utils
│   ├── data_loader.py
│   ├── mean_var_online.py
│   ├── metrics.py
│   ├── preprocess.py
│   └── utils.py
├── cnn_attack.ipynb
├── collect_side-channel.ipynb
├── cpa_attack.ipynb
├── SNR.ipynb
└── template_attack.ipynb
```

## Installation

### Prerequisites

Python 3.9 or higher. Install using:

   ```bash
   sudo apt install python3
   sudo apt install pip
   ```

Create a Python enviroment named `sca`:

1. Install pyenv (skip if already done):

   ```bash
   curl https://pyenv.run | bash
   echo 'export PATH="~/.pyenv/bin:$PATH"' >> ~/.bashrc
   echo 'export PATH="~/.pyenv/shims:$PATH"' >> ~/.bashrc
   echo 'eval "$(pyenv init -)"' >> ~/.bashrc
   echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

   source ~/.bashrc
   ```

2. Create an enviroment (choose Python 3.9 or higher):

   ```bash
   pyenv install 3.11.7
   pyenv virtualenv 3.11.7 sca
   ```

3. Activate the enviroment:

   ```bash
   pyenv activate sca
   ```

Intall Python packages requirements:

1. Install project dependencies:

   ```bash
   pip install -r requirements.txt
   # Compile source code
   cd ciphers/lib
   chmod +x compile_shared_objects.sh
   ./compile_shared_objects.sh
   ```

### Chipwhisperer Software Installation

1. Follow the [guide](https://chipwhisperer.readthedocs.io/en/latest/linux-install.html) to install the prerequisites for chipwhisperer for your operating system.
Use the created pyevn `sca`.

2. Install chipwhisperer module on Python

   ```bash
   python -m pip install chipwhisperer
   ```

### PicoScope Library Installation

Follow the steps below to install the PicoScope library on your Linux system. More details can be found [here](https://www.picotech.com/downloads/linux).

1. Add repository to the updater:

   ```bash
   sudo bash -c 'echo "deb https://labs.picotech.com/debian/ picoscope main" >> /etc/apt/sources.list.d/picoscope.list' 
   ``` 

2. Import the public key:

   ```bash
   wget -O - https://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add - 
   ```

3. Update the package manager cache:

   ```bash
   sudo apt-get update
   ```

4. Install PicoScope:

   ```bash
   sudo apt-get install picoscope
   ```

5. Install drivers:

   ```bash
   sudo apt-get install libps5000a
   ```

6. Check out the examples of C applications that use the PicoScope SDK [here](https://github.com/picotech/picosdk-c-examples)

### PicoSDK Python Wrappers Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/picotech/picosdk-python-wrappers
   ```

2. Install the python wrappers:

   ```bash
   cd picosdk-python-wrappers
   python setup.py install
   ```

   or for a user-specific installation:

   ```bash
   cd picosdk-python-wrappers
   python setup.py install --user
   ```

### CUDA driver installation

Follow the official NVIDIA [guide](https://developer.nvidia.com/cuda-downloads) to install NVIDIA CUDA drivers for your platform.

   ## Note

   The CNN architecture is based on the ASCAD [repository](https://github.com/ANSSI-FR/ASCAD).
   The original paper can be found in [1] and [online](https://eprint.iacr.org/2018/053.pdf).

   > [1] Emmanuel, P., Remi, S., Ryad, B., Eleonora, C., & Cecile, D. (2018).
   > Study of deep learning techniques for side-channel analysis and introduction to ascad database.
   > CoRR, 1-45.
