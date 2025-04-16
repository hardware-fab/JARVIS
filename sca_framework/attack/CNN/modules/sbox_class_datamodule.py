"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import pytorch_lightning as pl
from torch.utils.data import DataLoader

from attack.CNN.datasets import SboxClassifierDataset


class SboxClassifierDataModule(pl.LightningDataModule):
    def __init__(self, data_dir, target_byte, batch_size, num_workers):
        super(SboxClassifierDataModule, self).__init__()

        self.data_dir = data_dir
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.target_byte = target_byte

    def prepare_data(self):
        pass

    def setup(self, stage=None):
        if stage == 'fit':
            self.train_set = SboxClassifierDataset(
                self.data_dir, self.target_byte)
            self.valid_set = SboxClassifierDataset(
                self.data_dir, self.target_byte, which_subset='valid')
        elif stage == 'test':
            self.test_set = SboxClassifierDataset(
                self.data_dir, self.target_byte, which_subset='test')
        else:
            raise Exception('Unsupported stage type')

    def train_dataloader(self):
        return DataLoader(self.train_set,
                          batch_size=self.batch_size,
                          num_workers=self.num_workers,
                          shuffle=True,
                          pin_memory=True)

    def val_dataloader(self):
        return [DataLoader(self.valid_set,
                           batch_size=self.batch_size,
                           num_workers=self.num_workers,
                           shuffle=False),]

    def test_dataloader(self):
        return DataLoader(self.test_set,
                          batch_size=self.batch_size,
                          num_workers=self.num_workers,
                          shuffle=False)
