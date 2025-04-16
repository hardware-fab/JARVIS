"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import numpy as np
import torch
import torch.nn as nn
import pytorch_lightning as pl
import neptune

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

import torchmetrics
from torchmetrics import F1Score as F1

import attack.CNN.models as models
from ciphers.aesSca import AesSca
from tqdm.auto import tqdm
from sca_utils import guessMetrics, sortPredictions


class SboxClassifier(pl.LightningModule):
    def __init__(self, module_config, target_byte=0, gpu=0):
        super(SboxClassifier, self).__init__()
        
        self.cipher = AesSca()
        self.byte = target_byte
        
        # Output for logging
        #-------------
        self.validation_step_outputs = []
        self.test_step_outputs = []
        #-------------

        # Build Model
        # -----------
        model_name = module_config['model']['name']
        model_config = module_config['model']['config']
        model_class = getattr(models, model_name)
        self.model = model_class(**model_config)
        # -----------

        # Define Loss
        # -----------
        loss_name = module_config['loss']['name']
        if 'config' in module_config['loss']:
            loss_config = module_config['loss']['config']
            if 'weight' in loss_config and 'Entropy' in loss_name:
                weights = loss_config['weight']
                class_weights = torch.FloatTensor(
                    weights).to(torch.device(f'cuda:{gpu}'))
                loss_config['weight'] = class_weights
        else:
            loss_config = {}
        loss_class = getattr(nn, loss_name)
        self.loss = loss_class(**loss_config)
        # -----------

        # Get Optimization Config
        # -----------------------
        self.optimizer_config = module_config['optimizer']
        if 'scheduler' in module_config:
            self.scheduler_config = module_config['scheduler']
        else:
            self.scheduler_config = None
        # -----------------------

        # Get metrics
        # -----------
        self.metrics = {}
        metric_configs = module_config['metrics']
        for metric_config in metric_configs:
            metric_name = metric_config['name']
            metric_conf = metric_config['config']
            if 'F1' in metric_name:
                metric_class = F1
            else:
                metric_class = getattr(torchmetrics, metric_name)
            metric = metric_class(**metric_conf)
            self.metrics[metric_name] = metric.to(torch.device(f'cuda:{gpu}'))
        # -----------

    def forward(self, x):
        return self.model(x)

    def step_batch(self, batch):
        x, y, m = batch
        y_hat = self(x)
        loss = self.loss(y_hat, y)
        return {'loss': loss, 'target': y.detach(), 'prediction': nn.functional.softmax(y_hat, dim=1).detach(), 'meta': m.detach()}

    def training_step(self, batch, batch_idx):
        outputs = self.step_batch(batch)
        self.log_step(outputs, which_subset='train')
        return outputs

    def validation_step(self, batch, batch_idx):
        outputs = self.step_batch(batch)
        self.validation_step_outputs.append(outputs)
        self.log_step(outputs, which_subset='valid')
        return outputs

    def test_step(self, batch, batch_idx):
        outputs = self.step_batch(batch)
        self.test_step_outputs.append(outputs)
        self.log_step(outputs, which_subset='test')
        return outputs

    def log_step(self, outputs, which_subset='train'):
        self.log(
            f"{which_subset}/loss", torch.nan_to_num(outputs['loss']), on_step=True, on_epoch=True, sync_dist=True)
        for metric_name in self.metrics:
            # Compute metric
            val = self.metrics[metric_name](torch.nan_to_num(
                outputs['prediction']), outputs['target'])
            # Log metric
            self.log(f'{which_subset}/{metric_name}', val,
                     on_step=True, on_epoch=True, sync_dist=True)

    def log_confusion_matrix(self, outputs, which_subset='valid'):
        target = torch.cat([output['target'] for output in outputs])
        softmax_preds = torch.cat([output['prediction'] for output in outputs])
        preds = torch.argmax(softmax_preds, dim=1)

        target = target.cpu().data.numpy()
        preds = preds.cpu().data.numpy()

        fig, axis = plt.subplots(figsize=(16, 12))
        ConfusionMatrixDisplay.from_predictions(target, preds, ax=axis)
        self.logger.experiment[f'{which_subset}/confusion_matrix'].log(
            neptune.types.File.as_image(fig))

    def full_ranks(self, predictions, metadata):
        f_ranks = []
        f_distance = []

        key_values = np.arange(0, 256)
        for k in tqdm(key_values, desc='Ranking', leave=False):
            key_filter = metadata[:, 1, self.byte] == k
            keys = metadata[key_filter][:, 1]
            predictions_perKey = predictions[key_filter]
            plains_perKey = metadata[key_filter][:, 0]

            mapping = [self.cipher.invAttackedIntermediate(plains_perKey, np.array(
                [i]*len(plains_perKey)), self.byte) for i in range(256)]
            key_proba = sortPredictions(
                predictions_perKey, np.array(mapping).T)
            atk_key_byte = self.cipher.attackedKeyByte(keys[0], self.byte)
            real_key_rank, real_key_distance = guessMetrics(
                np.log(key_proba), atk_key_byte)
            f_ranks.append(real_key_rank[-1])
            f_distance.append(real_key_distance)
        return f_ranks, f_distance

    def log_rank(self, outputs, which_subset='valid'):
        target = torch.cat([output['target'] for output in outputs])
        meta = torch.cat([output['meta'] for output in outputs])
        softmax_preds = torch.cat([output['prediction'] for output in outputs])

        target = target.cpu().data.numpy()
        softmax_preds = softmax_preds.cpu().data.numpy()
        meta = meta.cpu().data.numpy()

        f_ranks, f_distance = self.full_ranks(softmax_preds, meta)

        self.log(f'{which_subset}/guessing_entropy',
                 np.mean(f_ranks), sync_dist=True)
        self.log(f'{which_subset}/guessing_distance',
                 np.mean(f_distance), sync_dist=True)

    def on_validation_epoch_end(self):
        self.log_rank(self.validation_step_outputs, which_subset='valid')
        self.validation_step_outputs.clear()

    def on_test_epoch_end(self):
        self.log_rank(self.test_step_outputs, which_subset='test')
        self.test_step_outputs.clear()

    def configure_optimizers(self):
        optimizer_name = self.optimizer_config['name']
        optimizer_config = self.optimizer_config['config']
        optimizer_class = getattr(torch.optim, optimizer_name)

        optimizer = optimizer_class(
            self.parameters(), **optimizer_config)
        if self.scheduler_config is None:
            return optimizer
        else:
            scheduler_name = self.scheduler_config['name']
            scheduler_config = self.scheduler_config['config']
            scheduler_class = getattr(torch.optim.lr_scheduler, scheduler_name)
            self.scheduler = scheduler_class(
                optimizer, **scheduler_config)
            if 'interval' not in self.scheduler_config:
                self.scheduler_config['interval'] = 'epoch'
            return [optimizer], [{"scheduler": self.scheduler, 
                                  "interval": self.scheduler_config['interval'],
                                  "monitor": self.scheduler_config['monitor']}]
