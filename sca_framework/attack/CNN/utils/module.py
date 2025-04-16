"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import attack.CNN.modules as modules

def build_module(module_config, target_byte, gpu):
    module_name = module_config['module']['name']
    module_config = module_config['module']['config']
    module_class = getattr(modules, module_name)
    module = module_class(module_config, target_byte, gpu)
    return module