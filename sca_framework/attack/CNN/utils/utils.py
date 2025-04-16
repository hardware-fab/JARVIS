"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import os
from omegaconf import OmegaConf
import numpy as np

from sca_utils import highpass, aggregate

def preprocess(traces, filter, std, window, aggregate_n_sample):
    mean, var = std
    if filter:
        traces = highpass(traces)
    traces = (traces-mean)/np.sqrt(var)
    traces = traces[:, window[0]:window[1]]
    if aggregate_n_sample > 1:
        traces = aggregate(traces, aggregate_n_sample)
    return traces.astype(np.dtype("float32"), casting="safe")


def parse_arguments(config_dir):
    exp_config_file = os.path.join(
        config_dir, 'experiment.yaml')
    module_config_file = os.path.join(
        config_dir, 'module.yaml')
    data_config_file = os.path.join(
        config_dir, 'data.yaml')

    exp_config = OmegaConf.to_object(OmegaConf.load(exp_config_file))
    module_config = OmegaConf.to_object(OmegaConf.load(module_config_file))
    data_config = OmegaConf.to_object(OmegaConf.load(data_config_file))

    return exp_config, module_config, data_config


def get_experiment_config_dir(best_model_ckpt, exp_name):
    exps_dir = best_model_ckpt.split(exp_name)[0]
    configs_dir = os.path.join(exps_dir, exp_name, 'configs')
    config_dir = next(os.walk(configs_dir))[1][0]
    config_dir = os.path.join(configs_dir, config_dir)
    print("Experiment config directory: {}".format(config_dir))
    return config_dir
