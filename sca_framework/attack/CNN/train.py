"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

from .utils import (parse_arguments, build_neptune_logger, build_module,
                   build_datamodule, build_trainer, init_experiment_dir, save_experiment_configs)


def train(config_folder: str,
          gpu: int = 0) -> None:
    """
    Train a model using the given configuration files.

    Parameters
    ----------
    `config_folder` : str
        The folder where the configuration files are stored.
    `gpu` : int, optional
        The GPU to use for the training (default is 0).
        0 if you want to use the first GPU, 1 if you want to use the second GPU, and so on.
    """

    exp_config, module_config, data_config = parse_arguments(config_folder)
    exp_config = exp_config['experiment']
    # ----------------

    # Build Neptune Logger
    # --------------------
    neptune_logger, exp_name_id = build_neptune_logger(
        exp_config['name'], exp_config['tags'], exp_config['neptune_config_file'])
    # --------------------

    # Initialize Experiment Directory
    exp_dir = init_experiment_dir(exp_config, exp_name_id)

    # Save Experiment Config Files
    save_experiment_configs(exp_dir, config_folder)

    # Build Lightning Module
    # --------------------------
    pl_module = build_module(module_config,
                             data_config['datamodule']['config']['target_byte'],
                             gpu)
    # --------------------------

    # Build Lightning DataModule
    # --------------------------
    pl_datamodule = build_datamodule(data_config)
    # --------------------------

    # Build Trainer
    # -------------
    pl_trainer = build_trainer(exp_dir, exp_config, neptune_logger, gpu)
    # -------------

    # Fit
    # ---
    pl_trainer.fit(pl_module, pl_datamodule)
    # ---

    # Test
    # ----
    pl_trainer.test(pl_module.eval(),
                    datamodule=pl_datamodule, ckpt_path='best')
    # ----
