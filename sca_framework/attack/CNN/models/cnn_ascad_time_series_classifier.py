"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari

The CNN architecture has been adapted from the following repository:
https://github.com/ANSSI-FR/ASCAD

Original paper:
Emmanuel, P., Remi, S., Ryad, B., Eleonora, C., & Cecile, D. (2018).
Study of deep learning techniques for side-channel analysis and introduction to ascad database.
CoRR, 1-45.
"""

import torch.nn as nn
from .cnn_ascad import CNNASCAD


class CNNASCADTimeSeriesClassifier(nn.Module):
    def __init__(self, classifier_params, encoder_params):
        super(CNNASCADTimeSeriesClassifier, self).__init__()

        self.encoder = CNNASCAD(**encoder_params)

        self.classifier = nn.Linear(self.encoder.encoding_size,
                                    classifier_params['out_channels'])

    def forward(self, x):
        x = x.view(x.size(0), 1, x.size(1))
        x = self.encoder(x)
        x = self.classifier(x)
        return x
