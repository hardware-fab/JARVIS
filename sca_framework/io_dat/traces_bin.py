"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)

Other contributor(s):  
    Giuseppe Diceglie
"""

import numpy as np
from picosdk.functions import adc2mV


def check_mV(head_size: int) -> bool:
    """
    Check if the trace file header contains enough information to convert the traces to millivolts.

    Parameters
    ----------
    `head_size` : int
        The size of the header in bytes.

    Return
    ------
    `False`
        If the header size is not 29, which means the header does not contain the channel range and
        the maximum ADC value needed for the conversion.
    `True`
        If the header size is 29, which means the header does contain the channel range and
        the maximum ADC value needed for the conversion.
    """

    return head_size == 29


class TracesBin:
    """
    A class used to read and handle binary files that contain traces,
    plaintextes and key.

    Attributes
    ----------
    `HEAD_SIZE` : int
        The size of the header.

    Methods
    -------
    `getAllTraces(mV)`:
        Get the whole batch of traces and plaintexts in order.

    `getTraces(idx, mV)`:
        Get the traces and plaintexts with the specified index.

    `getSamples(trace_idx, samples_idx, mV)`:
        Get the samples and plaintexts of the traces with the specified index and sample index.

    `getKey()`:
        Get the used key.

    `getNTraces()`:
        Get the total number of traces.

    `getNSamples()`:
        Get the number of sample per trace.
    """
    
    def __init__(self, filepath: str):
        """
        Open the binary file that contains the traces.

        Parameters
        ----------
        `filepath`: str
            the path of the .dat binary file.
        """

        self.__filepath = filepath

        with open(self.__filepath, "rb") as infile:
            # read header
            self.__ntraces = int.from_bytes(
                infile.read(4), byteorder="little", signed=False)
            self.__nsamples = int.from_bytes(
                infile.read(4), byteorder="little", signed=False)
            self.__sampletype = infile.read(1).decode("ascii")

            if self.__sampletype == "f":
                self.__sample_dtype = np.dtype("float32")
                self.HEAD_SIZE = 26
            elif self.__sampletype == "d":
                self.__sample_dtype = np.dtype("float64")
                self.HEAD_SIZE = 26
            elif self.__sampletype == "s":
                self.__sample_dtype = np.dtype("int16")
                self.__chRange = int.from_bytes(
                    infile.read(1), byteorder="little", signed=False)
                self.__maxADC = int.from_bytes(
                    infile.read(2), byteorder="little", signed=True)
                self.HEAD_SIZE = 29
            else:
                raise ValueError(f"Unknown sample type {self.__sampletype}. Expected 'f', 'd' or 's'.")

            self.__textlen = int.from_bytes(
                infile.read(1), byteorder="little", signed=False)
            self.__rowlen = (
                self.__textlen + self.__nsamples * self.__sample_dtype.itemsize)

            self.__key = np.frombuffer(buffer=infile.read(16), dtype="uint8")

    def getAllTraces(self,
                     mV: bool = False
                     ) -> tuple[np.ndarray, np.ndarray]:
        """
        Get the whole batch of traces and plaintexts in order.

        Parameters
        ----------
        `mV` : bool, optional
            A boolean that indicates whether the traces should be converted to millivolts
            or not (default is False).

        Returns
        -------
        traces : array_like, shape=(#traces, #samples)
            Traces corresponding to the index array, with each row being a trace of #samples samples.
        texts : array_like, shape=(#traces, 16)
            Plaintexts corresponding to the index array, with each row being a plaintext of 16 bytes.

        Raises
        ------
        `AssertionError`
            If the header does not contain the information needed for the conversion to milliVolt.
        """

        with open(self.__filepath, "rb") as infile:
            infile.seek(self.HEAD_SIZE, 0)

            texts = np.zeros((self.__ntraces, self.__textlen), dtype="uint8")
            traces = np.zeros(
                (self.__ntraces, self.__nsamples), dtype=self.__sample_dtype)

            for i in np.arange(0, self.__ntraces):
                traces[i, :] = np.frombuffer(
                    buffer=infile.read(self.__nsamples *
                                       self.__sample_dtype.itemsize),
                    dtype=self.__sample_dtype)
                texts[i, :] = np.frombuffer(
                    buffer=infile.read(self.__textlen* texts.itemsize),
                    dtype=texts.dtype)

        if self.__sample_dtype.type != np.float64:
            traces = traces.astype(np.dtype("float32"), casting="safe")
        if mV:
            assert check_mV(self.HEAD_SIZE), \
                "Cannot convert to milliVolt, no enough information in the file header!"
            traces = adc2mV(traces, self.__chRange, self.__maxADC)
        return traces, texts

    def getTraces(self,
                  idx: list[int],
                  mV: bool = False
                  ) -> tuple[np.ndarray]:
        """
        Get the traces and plaintexts with the specified index.
        Index can be an array of integers

        Parameters
        ----------
        `idx` : list[int]
            List of integers that specifies the index of the traces and plaintexts to be
            retrieved from the file.
        `mV` : bool, optional
            A boolean that indicates whether the traces should be converted to millivolts
            or not (default is False).

        Returns
        -------
        `traces` : array_like, shape=(n, #samples)
            Traces corresponding to the index array, with each row being a trace of #samples samples.
        `texts` : array_like, shape=(n, 16)
            Plaintexts corresponding to the index array, with each row being a plaintext of 16 bytes.

        Raises
        ------
        `AssertionError` :
            If any value in the index array is not a valid integer or is greater than or equal
            to the number of traces in the file (self.__ntraces).
        `AssertionError` :
           If the header does not contain the information needed for the conversion to milliVolt.
        """
        # check that all indexes are possible
        indexes = np.array(idx)

        assert np.all(indexes < self.__ntraces)
        assert np.all(indexes.dtype == "int")

        n = len(indexes)

        texts = np.zeros((n, self.__textlen), dtype="uint8")
        traces = np.zeros((n, self.__nsamples), dtype=self.__sample_dtype)
        with open(self.__filepath, "rb") as infile:
            j = 0
            for i in indexes:
                infile.seek(self.HEAD_SIZE + self.__rowlen * i, 0)
                traces[j, :] = np.frombuffer(
                    buffer=infile.read(self.__nsamples *
                                       self.__sample_dtype.itemsize),
                    dtype=self.__sample_dtype)
                texts[j, :] = np.frombuffer(
                    buffer=infile.read(self.__textlen * texts.itemsize),
                    dtype=texts.dtype)
                j = j + 1

        if self.__sample_dtype.type != np.float64:
            traces = traces.astype(np.dtype("float32"), casting="safe")
        if mV:
            assert check_mV(self.HEAD_SIZE), \
                "Cannot convert to milliVolt, no enough information in the file header!"
            traces = adc2mV(traces, self.__chRange, self.__maxADC)

        return traces, texts

    def getSamples(self,
                   trace_idx: list[int],
                   samples_idx: list[int],
                   mV: bool = False
                   ) -> tuple[np.ndarray]:
        """
        Get the samples and plaintexts of the traces with the specified index and sample index.

        Parameters
        ----------
        `trace_idx` : list[int]
            List of integers that specifies the index of the traces to be retrieved from the file.
        `samples_idx` : list[int]
            List of integers that specifies the index of the samples to be retrieved from each trace.
        `mV` : bool, optional
            A boolean that indicates whether the samples should be converted to millivolts
            or not (default is False).

        Returns
        -------
        `samples` : array_like, shape=(n, s)
            A matrix containing the samples corresponding to the trace index and
            sample index arrays, with each row being a subset of samples from a trace.
        `texts` : array_like, shape=(n, 16)
            A matrix containing the plaintexts corresponding to the trace index
            array, with each row being a plaintext of 16 bytes.

        Raises
        ------
        `AssertionError` :
            If any value in the trace index or sample index arrays is not a valid integer or is out of range.
        `AssertionError` :
            If the header does not contain the information needed for the conversion to milliVolt.
        """

        t_idx = np.array(trace_idx).reshape((len(trace_idx), 1))
        s_idx = np.array(samples_idx)

        n = len(trace_idx)
        s = len(samples_idx)

        traces = np.zeros((n, s), dtype=self.__sample_dtype)
        texts = np.zeros((n, self.__textlen), dtype="uint8")
        with open(self.__filepath, "rb") as infile:
            pos = (self.HEAD_SIZE
                   + t_idx * self.__rowlen
                   + s_idx * self.__sample_dtype.itemsize)
            for i in range(pos.shape[0]):
                for j in range(pos.shape[1]):
                    infile.seek(pos[i][j], 0)
                    traces[i, j] = np.frombuffer(
                        buffer=infile.read(self.__sample_dtype.itemsize),
                        dtype=self.__sample_dtype)

                infile.seek(self.HEAD_SIZE
                            + self.__rowlen * trace_idx[i]
                            + self.__nsamples * self.__sample_dtype.itemsize,
                            0)
                texts[i, :] = np.frombuffer(
                    buffer=infile.read(self.__textlen * texts.itemsize),
                    dtype=texts.dtype)

        if self.__sample_dtype.type != np.float64:
            traces = traces.astype(np.dtype("float32"), casting="safe")
        if mV:
            assert check_mV(self.HEAD_SIZE), \
                "Cannot convert to milliVolt, no enough information in the file header!"
            traces = adc2mV(traces, self.__chRange, self.__maxADC)

        return traces, texts

    def getKey(self) -> np.ndarray:
        """
        Get the used key.
        """
        return self.__key

    def getNTraces(self) -> int:
        """
        Get the total number of traces.
        """
        return self.__ntraces

    def getNSamples(self) -> int:
        """
        Get the number of sample per trace.
        """
        return self.__nsamples
