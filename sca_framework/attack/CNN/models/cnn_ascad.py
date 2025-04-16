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
import torch.nn.functional as F


class CNNASCAD(nn.Module):
    """
    1D ResNet encoder

    Input:
        X: (n_samples, n_channels, n_length)
        Y: (n_samples)

    Output:
        out: (n_samples)
    """

    def __init__(self, in_size, in_channels, base_filters, kernel_size, encoding_size, use_dropout, dropout):
        super(CNNASCAD, self).__init__()

        self.use_dropout = use_dropout
        self.encoding_size = encoding_size

        # Encoder
        # -------

        # Layer 1
        self.conv1 = nn.Conv1d(in_channels, base_filters,
                               kernel_size=kernel_size, padding='same')
        self.relu1 = nn.LeakyReLU()
        self.max_pool1 = nn.AvgPool1d(2)
        self.dropout1 = nn.Dropout(dropout)

        # Layer 2
        self.conv2 = nn.Conv1d(base_filters, base_filters*2,
                               kernel_size=kernel_size, padding='same')
        self.relu2 = nn.LeakyReLU()
        self.bn2 = nn.BatchNorm1d(base_filters*2)
        self.max_pool2 = nn.AvgPool1d(2)
        self.dropout2 = nn.Dropout(dropout)

        # Layer 3
        self.conv3 = nn.Conv1d(
            base_filters*2, base_filters*4, kernel_size=kernel_size, padding='same')
        self.relu3 = nn.LeakyReLU()
        self.bn3 = nn.BatchNorm1d(base_filters*4)
        self.max_pool3 = nn.AvgPool1d(2)
        self.dropout3 = nn.Dropout(dropout)

        # Layer 4
        self.conv4 = nn.Conv1d(
            base_filters*4, base_filters*8, kernel_size=kernel_size, padding='same')
        self.relu4 = nn.LeakyReLU()
        self.bn4 = nn.BatchNorm1d(base_filters*8)
        self.max_pool4 = nn.AvgPool1d(2)
        self.dropout4 = nn.Dropout(dropout)

        # Layer 5
        self.conv5 = nn.Conv1d(
            base_filters*8, base_filters*8, kernel_size=kernel_size, padding='same')
        self.relu5 = nn.LeakyReLU()
        self.bn5 = nn.BatchNorm1d(base_filters*8)
        self.max_pool5 = nn.AvgPool1d(2)
        self.dropout5 = nn.Dropout(dropout)

        # FC layer 1
        self.fc = nn.Linear((in_size // 32) * base_filters * 8, encoding_size)
        self.fc_relu = nn.LeakyReLU()
        # self.fc_relu = nn.Tanh()
        self.fc_bn = nn.BatchNorm1d(encoding_size)
        self.fc_dropout = nn.Dropout(dropout*0.8)
        # -------

    def forward(self, x):
        out = x

        # Layer 1
        out = self.conv1(out)
        out = self.relu1(out)
        out = self.max_pool1(out)
        if self.use_dropout:
            out = self.dropout1(out)

        # Layer 2
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.max_pool2(out)
        if self.use_dropout:
            out = self.dropout2(out)

        # Layer 3
        out = self.conv3(out)
        out = self.bn3(out)
        out = self.relu3(out)
        out = self.max_pool3(out)
        if self.use_dropout:
            out = self.dropout3(out)

        # Layer 4
        out = self.conv4(out)
        out = self.bn4(out)
        out = self.relu4(out)
        out = self.max_pool4(out)
        if self.use_dropout:
            out = self.dropout4(out)

        # Layer 5
        out = self.conv5(out)
        out = self.bn5(out)
        out = self.relu5(out)
        out = self.max_pool5(out)
        if self.use_dropout:
            out = self.dropout5(out)

        # Flattening
        out = out.view(out.size(0), -1)

        # FC layer 1
        out = self.fc(out)
        out = self.fc_bn(out)
        out = self.fc_relu(out)
        if self.use_dropout:
            out = self.fc_dropout(out)

        return out
