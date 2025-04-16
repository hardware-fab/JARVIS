"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

from abc import ABC, abstractmethod

class ADC(ABC):
    """
    Abstract class that represents an ADC device.
    """
    
    @abstractmethod
    def getMaxAdc(self):
        ...
    
    @abstractmethod
    def getChRange(self):
        ...
    
    @abstractmethod
    def getBatchSize(self):
        ...

    @abstractmethod
    def getSamplesPerSegment(self):
        ...

    def getSamplesPerChannel(self):
        pass

    def getTimeBaseNanoseconds(self):
        pass
    
    def getResolution(self):
        pass
