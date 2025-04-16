"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

from typing import Any
import numpy as np
from tqdm.auto import tqdm
from io_dat.traces_bin import TracesBin
from sca_utils import *
from ciphers import AesSca


class Snr():
    """
    Compute the Signal-to-Noise Ratio (SNR) of AES side-channel traces.
    The SNR is computed as the ratio between the variance of the signal and the variance of the noise.

    Methods
    ----------
    `update(traces, plains)`:
        Updates SNR's intermediate values with new `traces` and corresponding `plains`.
    `computeSnr()`:
        Compute the Signal-to-Noise Ratio.
    `fromFile(file, n_traces, chunk_size)`:
        Compute Signal-to-Noise Ratio starting from `file`.
    `getNTraces()`:
        Get the number of traces used to compute the SNR.
    """

    def __init__(self,
                 key: list[int],
                 target_byte: int = 0,
                 mode: str = "hw(sbox)",
                 filter: bool = False,
                 aggregate_n_samples: int = 1):
        """
        Parameters
        ----------
        `key`                : list[int]
            Key value corresponding to the side-channel traces.
        `target_byte`        : int, optional
            On which intermediate byte compute the SNR (default is 0).
        `mode`               : str, optional
            Leakage point on where to perform the attack (default is 'hw(sbox)').
        `filter`             : bool, optional
            Apply a highpass filter to traces as preprocessing (default is False).
        `aggregate_n_samples`: int, optional
            How many consecutive samples avarage together as preprocessing (default is 1).
        """

        self.key = key
        self._byte = target_byte
        self._mode = mode
        self._filter = filter
        self._aggregate_n_samples = aggregate_n_samples
        self.n_traces = 0

        self.__labels = np.arange(0, self._getNumClasses())

        self.__mean_var = [MeanVarOnline() for _ in self.__labels]

    def _classify(self, plains_byte, key_byte):
        mode = self._mode
        sbox = AesSca.attackedSbox(self._byte)
        if mode == "hw(sbox)":
            s = sbox[plains_byte ^ key_byte]
            class_index = hw[s]
        elif mode == "xor_bit":
            xor = plains_byte ^ key_byte
            class_index = xor >> 7
        elif mode == "sbox":
            s = sbox[plains_byte ^ key_byte]
            class_index = s
        elif mode == "xor_byte":
            xor = plains_byte ^ key_byte
            class_index = xor
        else:
            raise Exception(
                "Unknown mode. Choose between: hw(sbox), xor_bit, sbox, xor_byte.")

        return class_index

    def _getNumClasses(self):
        mode = self._mode
        if mode == "hw(sbox)":
            n_classes = 9
        elif mode == "xor_bit":
            n_classes = 2
        elif mode == "sbox":
            n_classes = 256
        elif mode == "xor_byte":
            n_classes = 256
        else:
            raise Exception(
                "Unknown mode. Choose between: hw(sbox), xor_bit, sbox, xor_byte.")

        return n_classes

    def getNTraces(self) -> int:
        """
        Get the number of traces used to compute the SNR

        Returns
        ----------
        Number of traces used to compute the SNR.
        """
        return self.n_traces

    def update(self,
               traces: np.ndarray,
               plains: np.ndarray):
        """
        Updates SNR's intermediate values with new `traces` and corresponding `plains`.

        Parameters
        ----------
        `traces`: array_like
            Traces to compute the SNR
        `plains`: array_like
            Plaintexts corresponding to traces
        """

        # Preprocess traces
        traces = self.__preprocess(traces)

        # Compute labels to divide the data
        labels_set = self._classify(
            plains[:, self._byte], self.key[self._byte])
        for label in self.__labels:
            grouped_traces = traces[labels_set == label]
            self.__mean_var[label].update(grouped_traces)
        self.n_traces += traces.shape[0]

    def computeSnr(self) -> np.ndarray:
        """
        Compute the Signal-to-Noise Ratio.

        Returns
        ----------
        Signal-to-Noise Ratio value.
        """
        signal_trace = []
        noise_trace = []

        for label in self.__labels:
            _, mean, var = self.__mean_var[label].finalize()
            noise_trace.append(var)
            signal_trace.append(mean)

        var_noise = np.mean(np.array(noise_trace), axis=0)
        var_signal = np.var(np.array(signal_trace), axis=0)
        snr_trace = var_signal/var_noise
        return snr_trace

    def fromFile(self,
                 file: str,
                 n_traces: int = None,
                 chunk_size: int = 10_000
                 ) -> np.ndarray:
        """
        Compute Signal-to-Noise Ratio starting from `file`.
        Signal intermediate depends by `cipher`.

        Parameters
        ----------
        `file`       : str
            File path containg the analyzed traces, in .dat format.
        `n_traces`   : int, optional
            How many traces use to analyze (default uses all traces in file).
        `chunk_size` : int, optional
            How many traces load into RAM each iteration (default is 10_000).

        Returns
        ----------
        Signal-to-Noise Ratio value.
        """

        traces_bin = TracesBin(file)
        N = n_traces if n_traces else traces_bin.getNTraces()
        dataLoader = self.__dataLoader(file, n_traces, chunk_size)

        for traces, plains in tqdm(dataLoader, total=int(np.ceil(N/chunk_size)), desc='Chunk processing'):
            self.update(traces, plains)
            del traces
            del plains

        # Compute SNR value
        snr_traces = self.computeSnr()

        return snr_traces

    def __dataLoader(self,
                     file: str,
                     n_traces: int = None,
                     chunk_size: int = 10_000):
        traces_bin = TracesBin(file)
        N = n_traces if n_traces else traces_bin.getNTraces()
        idx = 0
        while idx < N:
            if idx+chunk_size < N:
                stop_idx = idx+chunk_size
            else:
                stop_idx = N

            t, plains = traces_bin.getTraces(np.arange(idx, stop_idx))
            idx += chunk_size

            yield t, plains

    def __preprocess(self, traces):
        if self._aggregate_n_samples > 1:
            traces = aggregate(traces, self._aggregate_n_samples)
        if self._filter:
            traces = highpass(traces)
        return traces
