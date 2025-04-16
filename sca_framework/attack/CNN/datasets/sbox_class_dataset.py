"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import os
import numpy as np
from torch.utils.data import Dataset


class SboxClassifierDataset(Dataset):
    def __init__(self, data_dir, target_byte=0, which_subset='train'):

        self.target_byte = target_byte

        self.windows = np.load(
            os.path.join(data_dir, f'{which_subset}_windows.npy'), mmap_mode='r')

        self.target = np.load(
            os.path.join(data_dir, f'{which_subset}_targets.npy'), mmap_mode='r')
        
        self.meta = np.load(
            os.path.join(data_dir, f'{which_subset}_meta.npy'), mmap_mode='r')

        self.which_subset = which_subset
    
    def __len__(self):
        return self.target.shape[0]
    
    def __getitem__(self, index):
        x = self.windows[index]

        # Normalize x (mean 0, std 1)
        x = (x - np.mean(x)) / np.std(x)
        
        y = self.target[index, self.target_byte]
        m = self.meta[index, :]
        
        return x.copy(), y, m.copy()