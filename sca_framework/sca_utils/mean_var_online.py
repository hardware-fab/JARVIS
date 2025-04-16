"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

from .utils import kahanSum
import numpy as np

class MeanVarOnline():
    """
    A class used to compute the mean and variance of a stream of data online, feature-wise.
    Computation is done using the Kahan summation algorithm.
    
    Methods
    -------
    `reset()`:
        Resets the statistics and intermediate values.
    `update(newData)`:
        Updates the statistics with the given data.
    `finalize()`:
        Finalizes the statistics and returns the mean and variance.
    """

    def __init__(self):
        """
        Computes the mean and variance of a stream of data online, feature-wise.
        Computation is done using the Kahan summation algorithm.
        """
        
        self.n_traces = 0

    def reset(self,
              nFeature: int):
        """
        Resets the statistics and intermediate values.
        
        Parameters
        ----------
        `nFeature` : int
            The number of features to track.
        """
        self._mean = np.zeros((nFeature,), dtype='float64')
        self._c_mean = np.zeros((nFeature,), dtype='float64')
        self._M2 = np.zeros((nFeature,), dtype='float64')
        self._c_M2 = np.zeros((nFeature,), dtype='float64')

    def update(self,
               newData: np.ndarray):
        """
        Updates the statistics with the given data.

        Parameters
        ----------
        `newData` : array_like
            The array of data to update the statistics with.
        """
        
        if self.n_traces == 0:
            self.reset(newData.shape[1])
        
        for data in newData:
            self._existingAggregate = self._step(data)

    def _step(self,
              newValue):
        self.n_traces += 1
        delta = newValue - self._mean
        self._mean, self._c_mean = kahanSum(
            self._mean, self._c_mean, delta / self.n_traces)
        delta2 = newValue - self._mean
        self._M2, self._c_M2 = kahanSum(self._M2, self._c_M2, delta * delta2)

    def finalize(self) -> tuple[int, np.ndarray, np.ndarray]:
        """
        Finalizes the statistics and returns the mean and variance.

        Returns
        ----------
        A tuple containing the number of traces, mean, and variance.
        """
        if self.n_traces < 2:
            return self.n_traces, float("nan"), float("nan")
        else:
            self._variance = self._M2 / self.n_traces
            return self.n_traces, self._mean, self._variance
