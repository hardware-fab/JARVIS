"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import attack.CNN.modules as modules


def build_datamodule(data_config):
    datamodule_name = data_config['datamodule']['name']
    datamodule_config = data_config['datamodule']['config']
    dataset_dir = datamodule_config['dataset_dir']
    batch_size = datamodule_config['batch_size']
    num_workers = datamodule_config['num_workers']
    target_byte = datamodule_config['target_byte']

    datamodule_class = getattr(modules, datamodule_name)
    datamodule = datamodule_class(
        dataset_dir, target_byte, batch_size, num_workers)
    return datamodule
