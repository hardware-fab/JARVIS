"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)

Other contributor(s):  
    Giuseppe Diceglie
"""

import ctypes
from .adc import ADC


class OutputWriter():
    """
    A class to handle .dat files for PicoScope acquisitions.

    Methods
    -------
    `writeDatHeader(batchNumber, key)`:
        Write the header of the trace file with the given batch number and key.
    `writeDatHeaderCustom(batchsize, batchNumber, key)`:
        Write the header of the trace file with the given batch size, batch number and key.
    `writeMemorySegments(memorySegments, plaintexts):
        Append the memory segments and plaintexts to the trace .dat file.
    `writeAveraging(averaging, plaintexts)`:
        Write the averaging and plaintexts to the trace file.

    """

    def __init__(self, filename: str, adc: ADC):
        """
        Initialize an OutputWriter object to handle .dat files for PicoScope acquisitions.

        Parameters
        ----------
        `filename`  : str
            The name of the .dat file to be created.
        `adc` : ADC
            An ADC object that represents the device used to capture the traces.
        """

        self.__filename = filename
        self.__mSamplesPerSegment = adc.getSamplesPerSegment()
        self.__mSampleFormat = 's'
        self.__mPlaintextLength = 16
        self.__chRange = adc.getChRange('A')
        self.__maxADC = adc.getMaxAdc()

    def writeDatHeader(self,
                       key: int):
        """
        Write the header of the .dat file with the given encryption key.

        Parameters
        ----------
        `key` : int
            The encryption key used for the plaintexts.
        """

        numTotalTraces = ctypes.c_uint32(0)
        numSamples = ctypes.c_uint32(self.__mSamplesPerSegment)
        sampleFormat = ctypes.c_uint8(ord(self.__mSampleFormat))
        chRange = ctypes.c_uint8(self.__chRange)
        plaintextLength = ctypes.c_uint8(self.__mPlaintextLength)

        with open(self.__filename, "wb") as __mOstream:
            __mOstream.write(numTotalTraces)
            __mOstream.write(numSamples)
            __mOstream.write(sampleFormat)
            __mOstream.write(chRange)
            __mOstream.write(self.__maxADC)
            __mOstream.write(plaintextLength)
            __mOstream.write(key.to_bytes(16, 'big'))

    def writeMemorySegments(self,
                            memorySegments: list[ctypes.c_int16],
                            plaintexts: list[int]):
        """
        Append the memory segments and plaintexts to the .dat file.

        Parameters
        ----------
        `memorySegments` : list[ctypes.c_int16]
            A list of memory segments, each containing a list of samples.
        `plaintexts` : list[int]
            A list of plaintexts, each being an integer.

        Raises
        ------
        `AssertionError` :
            If the length of memory segments and plaintexts are not equal.
        """

        # memorySegments is a ctypes matrix, but it can be interrogated as a normal list of lists
        numSegments = len(memorySegments)
        segmentSize = len(memorySegments[0])

        assert len(plaintexts) == numSegments

        if self.__mSampleFormat == 's':
            data = (ctypes.c_int16 * segmentSize)()

        plaintext = (ctypes.c_uint8 * self.__mPlaintextLength)()

        with open(self.__filename, "ab") as __mOstream:
            for i in range(0, numSegments):
                # cast to sampleFormat
                data[:] = memorySegments[i][:]
                plaintext[:] = plaintexts[i].to_bytes(
                    self.__mPlaintextLength, 'big')

                __mOstream.write(data)
                __mOstream.write(plaintext)
        self._updateNumTraces(numSegments)

    def writeAveraging(self,
                       averaging,
                       plaintexts: list[int]):
        """
        Write the averaging and plaintexts to the .dat file.

        Parameters
        ----------
        `averaging` : 
            An Averaging object that contains the averaged power traces.
        `plaintexts` : list[int]
            A list of plaintexts, each being an integer.
        """
        power_trace = (ctypes.c_float * averaging.getSegmentSize())()
        plaintext = (ctypes.c_uint8 * self.__mPlaintextLength)()

        with open(self.__filename, "ab") as __mOstream:
            for i in range(0, averaging.getNumSegments()):
                power_trace[:] = averaging[i]
                plaintext[:] = plaintexts[i].to_bytes(
                    self.__mPlaintextLength, 'big')

                __mOstream.write(power_trace)
                __mOstream.write(plaintext)
        self._updateNumTraces(averaging.getNumSegments())

    def _updateNumTraces(self,
                         numTraces: int):
        """
        Update the number of traces in the .dat file.

        Parameters
        ----------
        `numTraces` : int
            The number of traces just added in the .dat file.
        """
        with open(self.__filename, "r+b") as __mOstream:
            numTraces += int.from_bytes(
                __mOstream.read(4), byteorder="little", signed=False)
            __mOstream.seek(0)
            __mOstream.write(ctypes.c_uint32(numTraces))
