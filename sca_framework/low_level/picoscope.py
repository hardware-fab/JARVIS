"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)

Other contributor(s):  
    Giuseppe Diceglie
"""

from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
import ctypes
from io_dat.adc import ADC


class PicoScope(ADC):
    def __init__(self, resolution=12, amplified=False):
        """
        Constructor for PicoScope
        resolution: resolution of device. It can be (8, 12, 14, 15, 16) bits
        """
        if resolution == 8:
            dev_res = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_8BIT']
        elif resolution == 12:
            dev_res = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_12BIT']
        elif resolution == 14:
            dev_res = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_14BIT']
        elif resolution == 15:
            dev_res = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_15BIT']
        elif resolution == 16:
            dev_res = ps.PS5000A_DEVICE_RESOLUTION['PS5000A_DR_16BIT']
        else:
            raise RuntimeError("Resolution " + str(resolution) +
                               " is invalid, it can be (8, 12, 14, 15, 16).")

        # Create chandle and status ready for use
        self.__mHandle = ctypes.c_int16()
        status = ps.ps5000aOpenUnit(
            ctypes.byref(self.__mHandle), None, dev_res)

        assert_pico_ok(status)

        self.__devRes = dev_res
        self.__mBatchSize = 1
        self.__mSamplesPerChannel = 0
        self.__mSamplesPerSegment = 0
        self.__mTimebase = 1
        self.__mTimebaseNanoseconds = 1
        self.__amplified = amplified
        self.__chARange = None

    def __del__(self):
        # Stops the scope
        # Handle = chandle
        status = ps.ps5000aStop(self.__mHandle)
        assert_pico_ok(status)

        # Closes the unit
        # Handle = chandle
        status = ps.ps5000aCloseUnit(self.__mHandle)
        assert_pico_ok(status)

    def __configureChannels(self, chARange_key='PS5000A_500MV', chBRange_key='PS5000A_5V'):
        """
        Configure channel A and channel B
        chARange_key and chBRange_key can be:
             'PS5000A_10MV'
             'PS5000A_20MV',
             'PS5000A_50MV',
             'PS5000A_100MV',
             'PS5000A_200MV',
             'PS5000A_500MV',
             'PS5000A_1V',
             'PS5000A_2V',
             'PS5000A_5V',
             'PS5000A_10V',
             'PS5000A_20V',
             'PS5000A_50V',
             'PS5000A_MAX_RANGES'
        keys are autoexplicative (MV stands for MilliVolts and V stands for Volts)
         """
        coupling = ps.PS5000A_COUPLING["PS5000A_DC"]

        enable = 1
        analogue_offset_A = 0 if self.__amplified else -0.945
        analogue_offset_B = 0

        self.__chARange = ps.PS5000A_RANGE[chARange_key]
        self.__chBRange = ps.PS5000A_RANGE[chBRange_key]

        # configuring channel A
        status = ps.ps5000aSetChannel(self.__mHandle,
                                      ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"],
                                      enable,
                                      coupling,
                                      self.__chARange,
                                      analogue_offset_A)

        assert_pico_ok(status)

        # configuring channel B
        status = ps.ps5000aSetChannel(self.__mHandle,
                                      ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"],
                                      enable,
                                      coupling,
                                      self.__chBRange,
                                      analogue_offset_B)

        assert_pico_ok(status)

    def __disableEtsMode(self):
        # disable ETS (Equivalent Time Sampling)
        PS5000A_ETS_OFF = 0  # I don't find the enumeration class in python
        status = ps.ps5000aSetEts(self.__mHandle, PS5000A_ETS_OFF, 0, 0, None)
        assert_pico_ok(status)

    def setTimebase(self, timebase):
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int16()
        status = ps.ps5000aGetTimebase2(self.__mHandle, timebase, self.__mSamplesPerSegment, ctypes.byref(
            timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(status)

        self.__mTimebase = timebase
        self.__mTimebaseNanoseconds = timeIntervalns.value

    def getIdealBatchSize(self, duration_ns):
        samples = ctypes.c_int()
        status = ps.ps5000aMemorySegments(
            self.__mHandle, 1, ctypes.byref(samples))

        available_samples = samples.value >> 1
        assert_pico_ok(status)

        wanted_samples = int(duration_ns / self.__mTimebaseNanoseconds)

        batch_size = available_samples / wanted_samples

        return batch_size

    def __getChRange(self, chRange):
        if chRange == "10mv":
            return 'PS5000A_10MV'
        elif chRange == "20mv":
            return 'PS5000A_20MV'
        elif chRange == "50mv":
            return 'PS5000A_50MV'
        elif chRange == "100mv":
            return 'PS5000A_100MV'
        elif chRange == "200mv":
            return 'PS5000A_200MV'
        elif chRange == "500mv":
            return 'PS5000A_500MV'
        elif chRange == "1v":
            return 'PS5000A_1V'
        elif chRange == "2v":
            return 'PS5000A_2V'
        elif chRange == "5v":
            return 'PS5000A_5V'
        elif chRange == "10v":
            return 'PS5000A_10V'
        elif chRange == "20v":
            return 'PS5000A_20V'
        elif chRange == "50v":
            return 'PS5000A_50V'

    def getMaxAdc(self):
        maxADC = ctypes.c_int16()
        ps.ps5000aMaximumValue(self.__mHandle, ctypes.byref(maxADC))
        return maxADC

    def getChRange(self, channel='A'):
        return self.__chARange if channel == 'A' else self.__chBRange

    def __configureNumberOfCaptures(self):
        samples = ctypes.c_int()

        # Handle = self.__mHandle
        # nSegments = self.__mBatchSize
        # nMaxSamples = ctypes.byref(samples)
        status = ps.ps5000aMemorySegments(
            self.__mHandle, self.__mBatchSize, ctypes.byref(samples))
        assert_pico_ok(status)

        self.__mSamplesPerSegment = int(samples.value / 2)
        self.__mSamplesPerChannel = self.__mSamplesPerSegment * self.__mBatchSize

        # sets number of captures
        status = ps.ps5000aSetNoOfCaptures(self.__mHandle, self.__mBatchSize)
        assert_pico_ok(status)

    def __configureTrigger(self, trigger_channel='B', trigger_threshold_mv=2000, trigger_threshold_direction="rising"):
        # configure trigger channel (argument trigger_channel)
        if trigger_channel.upper() == 'A':
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
            chRange = self.__chARange
        elif trigger_channel.upper() == 'B':
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
            chRange = self.__chBRange
        else:
            raise RuntimeError("Invalid channel for trigger")

        # configure threshold (argument trigger_threshold_mv)
        # Finds the max ADC count
        maxADC = ctypes.c_int16()
        status = ps.ps5000aMaximumValue(self.__mHandle, ctypes.byref(maxADC))
        assert_pico_ok(status)

        # convert milliovlts to adc count
        threshold = int(mV2adc(trigger_threshold_mv, chRange, maxADC))

        # configure threshold direction (argument trigger_threshold_direction)
        if trigger_threshold_direction.upper() == "RISING":
            direction = ps.PS5000A_THRESHOLD_DIRECTION['PS5000A_RISING']
        elif trigger_threshold_direction.upper() == "FALLING":
            direction = ps.PS5000A_THRESHOLD_DIRECTION['PS5000A_FALLING']
        else:
            raise RuntimeError("Invalid trigger threshold direction")

        enable = 1
        trigger_delay = 0  # time between the trigger and the first sample captured
        auto_trigger_ms = 0  # wait indefinitely for a trigger event
        status = ps.ps5000aSetSimpleTrigger(
            self.__mHandle, enable, source, threshold, direction, trigger_delay, auto_trigger_ms)
        assert_pico_ok(status)

    def getResolution(self):
        if self.__devRes == 0:
            return 8
        elif self.__devRes == 1:
            return 12
        elif self.__devRes == 2:
            return 14
        elif self.__devRes == 3:
            return 15
        elif self.__devRes == 4:
            return 16
        else:
            return -1

    def setBatchSize(self, batch_size):
        self.__mBatchSize = batch_size

    def getBatchSize(self):
        return self.__mBatchSize

    def getSamplesPerSegment(self):
        return self.__mSamplesPerSegment

    def getSamplesPerChannel(self):
        return self.__mSamplesPerChannel

    def getTimeBaseNanoseconds(self):
        return self.__mTimebaseNanoseconds

    def setup(self, timebase, chArange="500mv"):
        self.__disableEtsMode()
        rangeA = self.__getChRange(chArange)
        self.__configureChannels(chARange_key=rangeA)
        self.setTimebase(timebase)
        self.__configureNumberOfCaptures()
        self.__configureTrigger()

    def run(self):
        pre_trigger_samples = 50
        post_trigger_samples = self.__mSamplesPerSegment - pre_trigger_samples

        segment_index = 0

        # Starts the block capture
        # Handle = mHandle
        # Number of prTriggerSamples
        # Number of postTriggerSamples
        # Timebase = mTimebase
        # time indisposed ms = None
        # Segment index = segment_index =0
        # LpRead = mCallback
        # pParameter = pParameter

        status = ps.ps5000aRunBlock(self.__mHandle, pre_trigger_samples, post_trigger_samples,
                                    self.__mTimebase, None, segment_index, None, None)

        assert_pico_ok(status)

    def stop(self):
        status = ps.ps5000aStop(self.__mHandle)
        assert_pico_ok(status)

    def getNumberCaptures(self):
        num = ctypes.c_uint32()
        status = ps.ps5000aGetNoOfCaptures(self.__mHandle, ctypes.byref(num))
        assert_pico_ok(status)
        return num.value

    def retrieveData(self, channel="A"):
        memorySegments = (
            ctypes.c_short * self.__mSamplesPerSegment * self.__mBatchSize)()

        if channel.upper() == "A":
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_A"]
        elif channel.upper() == "B":
            source = ps.PS5000A_CHANNEL["PS5000A_CHANNEL_B"]
        else:
            raise RuntimeError("Invelid channel name")

        for i in range(0, self.__mBatchSize):
            status = ps.ps5000aSetDataBuffer(self.__mHandle, source,
                                             ctypes.byref(memorySegments[i]),
                                             self.__mSamplesPerSegment, i,
                                             ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_NONE'])

            assert_pico_ok(status)

        memorySize = ctypes.c_int32(self.__mSamplesPerChannel)
        startSegment = 0
        endSegment = self.__mBatchSize - 1
        overflow = (ctypes.c_int16 * self.__mBatchSize)()

        # Checks data collection to finish the capture
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            status = ps.ps5000aIsReady(self.__mHandle, ctypes.byref(ready))

        status = ps.ps5000aGetValuesBulk(self.__mHandle, ctypes.byref(memorySize), startSegment, endSegment,
                                         0, ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_NONE'], ctypes.byref(overflow))

        return memorySegments

    def retrieveDatamV(self, channel="A"):
        data = self.retrieveData(channel)
        chRange = self.__chARange if channel == "A" else self.__chBRange
        maxADC = ctypes.c_int16()
        status = ps.ps5000aMaximumValue(self.__mHandle, ctypes.byref(maxADC))
        assert_pico_ok(status)
        return adc2mV(data, chRange, maxADC)
