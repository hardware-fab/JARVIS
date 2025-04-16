"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)

Other contributor(s):  
    Giuseppe Diceglie
"""

from .uart import Uart
from .riscv import *
import time
from sca_utils.utils import little2big

memoryMappedBitfield = {'tokenType': 6,
                        'selBits': 4, 'cti': 3, 'rw': 1, 'bte': 2}

duLocalBitfield = {'tokenType': 6, 'duId': 5}


class CommandBytes():
    def __init__(self, **kwargs):

        if kwargs.keys() == duLocalBitfield.keys():
            # it's a duLocal command
            bf = duLocalBitfield

        elif kwargs.keys() == memoryMappedBitfield.keys():
            # it's a memoryMapped command
            bf = memoryMappedBitfield

        else:
            assert False

        cmd = 0
        cur = 0

        for key in bf.keys():
            bits_n = bf.get(key)
            sub_cmd = kwargs.get(key)

            cmd = cmd | (sub_cmd % 2**bits_n) << cur
            cur = cur + bits_n

        self.__bytesCmd = cmd

    def getBytesCmd(self):
        return self.__bytesCmd


class TokenType:
    InvalidToken = 0

    MemoryMappedRead = 1
    MemoryMappedWrite = 2

    GprInt32Read = 3
    GprInt32Write = 4
    GprFpu32Read = 5
    GprFpu32Write = 6

    HaltCPU = 7
    ResumeCPU = 8
    ResetCPU = 9
    GetDuLocalState = 10
    GetPC = 11

    SetBreakPoint = 12
    GetBreakPoint = 13
    RemoveBreakPoint = 14
    GetBreakPointNumber = 15

    GetLowCycleCntLastRunPeriod = 16
    GetHighCycleCntLastRunPeriod = 17
    GetLowInstrCntLastRunPeriod = 18
    GetHighInstrCntLastRunPeriod = 19

    AdvanceOneStep = 20
    Echo = 21

    SetTriggerPoint = 22
    GetTriggerPoint = 23
    RemoveTriggerPoint = 24
    GetTriggerPointNumber = 25

    SetFrequency = 26
    GetFrequency = 27
    RndFrequency = 28


class Jarvis():
    """
    Class to communicate with the JARVIS SoC via UART.
    The class interacts with the JARVIS dedug unit by sending commands and receiving responses via UART.
    """
    
    cpuId = 0
    dfsId = 1

    def __init__(self,
                 path: str = "/dev/ttyUSB0"):
        """
        Create a new JARVIS object to communicate with the JARVIS SoC via UART.

        Parameters
        ----------
        `path`: str
            Path to the UART device.
        """
        self.__m_uart = Uart(path)
        self.__breakpoints = []
        self.__triggerpoints = []

    def __prepareBytes(self, cmd, *args):
        # cmd is 2 bytes
        # args are 4 bytes
        data = []
        cmd_bytes = cmd.to_bytes(2, 'big')

        data.append(cmd_bytes[0])
        data.append(cmd_bytes[1])

        # check argument length (1 or 2)
        assert len(args) > 0
        assert len(args) < 3

        arg1_bytes = args[0].to_bytes(4, 'big')
        data.append(arg1_bytes[0])
        data.append(arg1_bytes[1])
        data.append(arg1_bytes[2])
        data.append(arg1_bytes[3])

        if len(args) == 2:
            arg2_bytes = args[1].to_bytes(4, 'big')
            data.append(arg2_bytes[0])
            data.append(arg2_bytes[1])
            data.append(arg2_bytes[2])
            data.append(arg2_bytes[3])
        return data

    def isConnected(self):
        """
        Check if the connection is working.
        """
        cmd = CommandBytes(tokenType=TokenType.Echo, duId=0)

        writeBytes = self.__prepareBytes(cmd.getBytesCmd(), 0, 0)
        self.__m_uart.writeBytes(writeBytes)
        readBytes = self.__m_uart.readBytes(10)
        if (len(writeBytes) != len(readBytes)):
            return False
        for i in range(0, len(writeBytes)):
            if (writeBytes[i] != readBytes[i]):
                return False
        return True

    def __memoryRead(self, address):
        cmd = CommandBytes(tokenType=TokenType.MemoryMappedRead,
                           selBits=15,
                           rw=ReadWrite.Read,
                           cti=CTI.Classic,
                           bte=BTE.Linear
                           )

        writeBytes = self.__prepareBytes(cmd.getBytesCmd(), address)
        self.__m_uart.writeBytes(writeBytes)

        data = self.__readResponse(
            5, -1, "Could not read the specified address: '" + hex(address) + "'")
        return data

    def memoryReadByte(self,
                       address: int) -> int:
        """
        Read a byte from memory.

        Parameters
        ----------
        `address`: int
            Address of the byte to read.

        Returns
        ----------
        The byte read from the address.
        """
        cmd = CommandBytes(tokenType=TokenType.MemoryMappedRead,
                           selBits=0xF,
                           rw=ReadWrite.Read,
                           cti=CTI.Classic,
                           bte=BTE.Linear
                           )

        word_address = (address >> 2) << 2

        writeBytes = self.__prepareBytes(cmd.getBytesCmd(), word_address)
        self.__m_uart.writeBytes(writeBytes)
        data = self.__readResponse(
            5, -1, "Could not read the specified address: '" + hex(address) + "'")
        readBytes = data.to_bytes(4, "little")
        byte = readBytes[address % 4]

        return byte

    def memoryReadVariable(self,
                           address: int,
                           n_words: int) -> int:
        """
        Read a multi-word variable.

        Parameters
        ----------
        `address`: int
            Address of the variable.
        `n_words`: int
            Number of words the variable is composed of. (1 word== 4 bytes)

        Returns
        ----------
        The variable read from the address.
        """
        var = 0
        for i in range(0, n_words):
            var = var << 8*4
            var = var | little2big(self.__memoryRead(address+i*4), 4)
        return var

    def __memoryWrite(self, address, data):
        cmd = CommandBytes(tokenType=TokenType.MemoryMappedWrite,
                           selBits=0xF,
                           rw=ReadWrite.Write,
                           cti=CTI.Classic,
                           bte=BTE.Linear
                           )

        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), address, data)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, -1, "Could not write to the specified address: '" + hex(address) + "'")

    def memoryWriteByte(self,
                        address: int,
                        data: int) -> None:
        """
        Write a byte to memory.

        Parameters
        ----------
        `address`: int
            Address of the byte to write.
        `data`: int
            Byte to write.
        """
        mod = address % 4
        word_address = (address >> 2) << 2
        word_data = data << (mod << 3)

        cmd = CommandBytes(tokenType=TokenType.MemoryMappedWrite,
                           selBits=1 << mod,
                           rw=ReadWrite.Write,
                           cti=CTI.Classic,
                           bte=BTE.Linear
                           )

        bytesToWrite = self.__prepareBytes(
            cmd.getBytesCmd(), word_address, word_data)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, -1, "Could not write to the specified address: '" + hex(address) + "'")

    def memoryWriteVariable(self,
                            address: int,
                            n_words: int,
                            data: int):
        """
        Write a multi-word variable.

        Parameters
        ----------
        `address`: int
            Address of the variable.
        `n_words`: int
            Number of words the variable is composed of. (1 word== 4 bytes)
        `data`: int
            Variable to write.
        """
        for i in range(0, n_words):
            start = i*4
            stop = start+4
            var_bytes = data.to_bytes(n_words*4, 'big')
            self.__memoryWrite(
                address + 4*i, little2big(int.from_bytes(var_bytes[start:stop], 'big'), 4))

    def getPc(self,
              duId: int) -> int:
        """
        Get the program counter (PC) of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get the PC from.

        Returns
        ----------
        The PC of the specified CPU.
        """
        cmd = CommandBytes(tokenType=TokenType.GetPC, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not read the PC")
        return data

    def getGprInt(self,
                  duId: int,
                  gpr: str) -> int:
        """
        Get the value of an integer general purpose register (GPR) of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get the GPR from.
        `gpr`: str
            Name of the GPR to get the value from.

        Returns
        ----------
        The value of the specified GPR.
        """
        cmd = CommandBytes(tokenType=TokenType.GprInt32Read, duId=duId)
        gpr = Register.__dict__[gpr]
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), gpr)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not get INT GPR")

        return data

    def setGprInt(self,
                  duId: int,
                  gpr: str,
                  data: int) -> None:
        """
        Set the value of an integer general purpose register (GPR) of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set the GPR to.
        `gpr`: str
            Name of the GPR to set the value to.
        `data`: int
            Value to set the GPR to.
        """
        cmd = CommandBytes(tokenType=TokenType.GprInt32Write, duId=duId)
        gpr = Register.__dict__[gpr]
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), gpr, data)
        self.__m_uart.writeBytes(bytesToWrite)

        self.__readResponse(1, duId, "Could not write into INT GPR")

    def getGprFpu(self,
                  duId: int,
                  gpr: str) -> int:
        """
        Get the value of a floating point general purpose register (GRP) of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get the FPU from.
        `gpr`: str
            Name of the FPU register to get the value from.

        Returns
        ----------
        The value of the specified FPU register.
        """
        cmd = CommandBytes(tokenType=TokenType.GprFpu32Read, duId=duId)
        gpr = Register.__dict__[gpr]
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), gpr)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not get FPU GPR")

        return data

    def setGprFpu(self,
                  duId: int,
                  gpr: str,
                  data: int) -> None:
        """
        Set the value of a floating point general purpose register (GPR) of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set the FPU to.
        `gpr`: str
            Name of the FPU register to set the value to.
        `data`: int
            Value to set the FPU register to.
        """
        cmd = CommandBytes(tokenType=TokenType.GprFpu32Write, duId=duId)
        gpr = Register.__dict__[gpr]
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), gpr, data)
        self.__m_uart.writeBytes(bytesToWrite)

        self.__readResponse(1, duId, "Could not write into FPU GPR")

    def getCycleCntLastRun(self,
                           duId: int) -> int:
        """
        Get the cycle count of the last run period of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get the cycle count from.

        Returns
        ----------
        The cycle count of the last run period of the specified CPU.
        """
        cmd = CommandBytes(
            tokenType=TokenType.GetHighCycleCntLastRunPeriod, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        dataHigh = self.__readResponse(
            5, duId, "Could not get high cycle count")

        cmd = CommandBytes(
            tokenType=TokenType.GetLowCycleCntLastRunPeriod, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        dataLow = self.__readResponse(5, duId, "Could not get low cycle count")
        data = dataHigh << 32 | dataLow
        return data

    def getInstrCntLastRun(self,
                           duId: int) -> int:
        """
        Get the instruction count of the last run period of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get the instruction count from.

        Returns
        ----------
        The instruction count of the last run period of the specified CPU.
        """
        cmd = CommandBytes(
            tokenType=TokenType.GetHighInstrCntLastRunPeriod, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        dataHigh = self.__readResponse(
            5, duId, "Could not get high instruction count")

        cmd = CommandBytes(
            tokenType=TokenType.GetLowInstrCntLastRunPeriod, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        dataLow = self.__readResponse(
            5, duId, "Could not get low instruction count")
        data = dataHigh << 32 | dataLow
        return data

    def advanceOneStep(self,
                       duId: int) -> None:
        """
        Advance the specified CPU by one step., i.e., one clock cycle.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to advance.
        """
        cmd = CommandBytes(tokenType=TokenType.AdvanceOneStep, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), 0)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not advance one step")

        return data

    def haltCPU(self,
                duId: int) -> None:
        """
        Halt the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to halt.
        """
        cmd = CommandBytes(tokenType=TokenType.HaltCPU, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(5, duId, "Could not halt the cpu")

    def resetCPU(self,
                 duId: int) -> None:
        """
        Reset the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to reset.
        """
        cmd = CommandBytes(tokenType=TokenType.ResetCPU, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(5, duId, "Could not reset the cpu")

    def resumeCPU(self,
                  duId: int) -> None:
        """
        Resume the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to resume.
        """
        cmd = CommandBytes(tokenType=TokenType.ResumeCPU, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(5, duId, "Could not resume the cpu")

    def __getCPUState(self, duId):
        cmd = CommandBytes(tokenType=TokenType.GetDuLocalState, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(5, duId, "Could not get the state")

        if data == 1:
            state_name = "RESET"
        elif data == 7:
            state_name = "RUNNING"
        elif data == 11:
            state_name = "HALTED"
        else:
            state_name = "UNKNOWN"

        return state_name

    def isCPURunning(self,
                     duId: int) -> bool:
        """
        Check if the specified CPU is running.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to check.

        Returns
        ----------
        True if the CPU is running, False otherwise.
        """
        try:
            return self.__getCPUState(duId) == "RUNNING"
        except:
            return False

    def isCPUHalted(self,
                    duId: int) -> bool:
        """
        Check if the specified CPU is halted.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to check.

        Returns
        ----------
        True if the CPU is halted, False otherwise.
        """
        try:
            return self.__getCPUState(duId) == "HALTED"
        except:
            return False

    def isCPUReset(self,
                   duId: int) -> bool:
        """
        Check if the specified CPU is reset.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to check.

        Returns
        ----------
        True if the CPU is reset, False otherwise.
        """
        try:
            return self.__getCPUState(duId) == "RESET"
        except:
            return False

    def __getBreakPointNumber(self, duId):
        cmd = CommandBytes(tokenType=TokenType.GetBreakPointNumber, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(5, duId, "Could not get breakpoint number")

        return data

    def __getBreakPoint(self, duId):
        cmd = CommandBytes(tokenType=TokenType.GetBreakPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not get breakpoint")

        return data

    def getBreakPoints(self,
                       duId: int) -> list[int]:
        """
        Get the breakpoints of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get breakpoints from.

        Returns
        ----------
        A list of breakpoint addresses.
        """
        breakpoints = []
        breakpoint_number = self.__getBreakPointNumber(duId)
        for _ in range(0, breakpoint_number):
            brk = self.__getBreakPoint(duId)
            breakpoints.append(brk)

        return breakpoints

    def setBreakPoint(self,
                      duId: int,
                      pc: int) -> None:
        """
        Set a breakpoint at the specified address for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set breakpoint for.
        `pc`: int
            Address to set the breakpoint at.
        """
        cmd = CommandBytes(tokenType=TokenType.SetBreakPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId, pc)

        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, duId, "Could not set breakpoint at address " + hex(pc))
        self.__breakpoints.append(pc)

    def setBreakPoints(self,
                       duId: int,
                       breakpoints: list[int]) -> None:
        """
        Set multiple breakpoints at the specified addresses for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set breakpoints for.
        `brks`: list[int]
            Addresses to set the breakpoints at.
        """
        for pc in breakpoints:
            self.setBreakPoint(duId, pc)

    def removeBreakPoint(self,
                         duId: int,
                         pc: int) -> None:
        """
        Remove the breakpoint at the specified address for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to remove breakpoint from.
        `pc`: int
            Address to remove the breakpoint from.
        """
        cmd = CommandBytes(tokenType=TokenType.RemoveBreakPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId, pc)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, duId, "Could not remove breakpoint at address " + hex(pc))
        self.__breakpoints.remove(pc)

    def removeBreakPoints(self,
                          duId: int) -> None:
        """
        Remove all breakpoints from the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to remove breakpoints from.
        """
        for brk in self.getBreakPoints(duId):
            self.removeBreakPoint(duId, brk)

    def waitForBreakPoint(self,
                          duId: int,
                          interval_us: int) -> None:
        """
        Wait for the specified CPU to reach a breakpoint.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to wait.
        `interval_us`: int
            Time to wait in microseconds.
        """
        while (not self.isCPUHalted(duId)):
            time.sleep(0.000001 * interval_us)

    def __getTriggerPointNumber(self, duId):
        cmd = CommandBytes(
            tokenType=TokenType.GetTriggerPointNumber, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(
            5, duId, "Could not get triggerpoint number")
        return data

    def __getTriggerPoint(self, duId):
        cmd = CommandBytes(tokenType=TokenType.GetTriggerPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId)
        self.__m_uart.writeBytes(bytesToWrite)

        data = self.__readResponse(5, duId, "Could not get triggerpoint")
        return data

    def getTriggerPoints(self,
                         duId: int) -> list[int]:
        """
        Get the triggerpoints of the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to get triggerpoints from.

        Returns
        ----------
        A list of triggerpoint addresses.
        """
        triggers = []
        trigger_number = self.__getTriggerPointNumber(duId)
        for i in range(0, trigger_number):
            trg = self.__getTriggerPoint(duId)
            triggers.append(trg)

        return triggers

    def setTriggerPoint(self,
                        duId: int,
                        pc: int) -> None:
        """
        Set a triggerpoint at the specified address for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set triggerpoint for.
        `pc`: int
            Address to set the triggerpoint at.
        """
        cmd = CommandBytes(tokenType=TokenType.SetTriggerPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId, pc)

        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, duId, "Could not set triggerpoint at address " + hex(pc))
        self.__triggerpoints.append(pc)

    def setTriggerPoints(self,
                         duId: int,
                         triggers: list[int]) -> None:
        """
        Set multiple triggerpoints at the specified addresses for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to set triggerpoints for.
        `triggers`: list[int]
            Addresses to set the triggerpoints at.
        """
        for pc in triggers:
            self.setTriggerPoint(duId, pc)

    def removeTriggerPoint(self,
                           duId: int,
                           pc: int) -> None:
        """
        Remove the triggerpoint at the specified address for the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to remove triggerpoint from.
        `pc`: int
            Address to remove the triggerpoint from.
        """
        cmd = CommandBytes(tokenType=TokenType.RemoveTriggerPoint, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), duId, pc)
        self.__m_uart.writeBytes(bytesToWrite)
        self.__readResponse(
            1, duId, "Could not remove triggerpoint at address " + hex(pc))
        self.__triggerpoints.remove(pc)

    def removeTriggerPoints(self,
                            duId: int) -> None:
        """
        Remove all triggerpoints from the specified CPU.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to remove triggerpoints from.
        """
        for trg in self.getTriggerPoints(duId):
            self.removeTriggerPoint(duId, trg)

    def setFrequency(self,
                     duId: int,
                     frequency: float) -> None:
        """
        Set the frequency of the specified DFS.

        Parameters
        ----------
        `duId`: int
            DFS's debug unit ID to set.
        `frequency`: float
            Frequency to set the DFS to.
        """
        cmd = CommandBytes(tokenType=TokenType.SetFrequency, duId=duId)
        bytesToWrite = self.__prepareBytes(
            cmd.getBytesCmd(), 0, int(frequency*8))
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(
            1, duId, "Could not set frequency to" + str(frequency))
        return data

    def rndFrequency(self,
                     duId: int) -> None:
        """
        Set the specified DFS to a randomly change the frequency.

        Parameters
        ----------
        `duId`: int
            DFS's debug unit ID to set.
        """
        cmd = CommandBytes(tokenType=TokenType.RndFrequency, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), 0, 0)
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(1, duId, "Could not set random frequency")
        return data

    def getFrequency(self,
                     duId: int) -> float:
        """
        Get the frequency of the specified DFS.

        Parameters
        ----------
        `duId`: int
            DFS's debug unit ID to get.

        Returns
        ----------
        The frequency of the specified DFS.
        """
        cmd = CommandBytes(tokenType=TokenType.GetFrequency, duId=duId)
        bytesToWrite = self.__prepareBytes(cmd.getBytesCmd(), 0)
        self.__m_uart.writeBytes(bytesToWrite)
        data = self.__readResponse(5, duId, "Could not get frequency")
        freq = data / 8
        return freq

    def loadBinary(self,
                   filename: str) -> None:
        """
        Load a binary file to the memory.

        Parameters
        ----------
        `filename`: str
            Path of the binary file to load.
        """
        try:
            ifile = open(filename, "r")
            line = ifile.readline()
            while line:
                address = int(line[1:1+8], base=16)
                data = int(line[10:10+8], base=16)

                self.__memoryWrite(address << 2, data)
                line = ifile.readline()

            ifile.close()

        except IOError:
            raise RuntimeError("Could not find the binary" + filename)

    def __readResponse(self, n, duId, error_msg):
        """
        read the response from uart
        first byte is the ok/ko code, the rest is the data I'm getting

        n: number of bytes to read
        duId: cpu I'm using. -1 for mmap operations
        error_msg: message to display if there is an arrer
        """
        assert n > 0

        bytesRead = self.__m_uart.readBytes(n)
        if bytesRead[0] == 3:  # ko code
            o = "CPU '" + str(duId) + "': " + error_msg
            raise RuntimeError(o)

        data = 0
        for i in range(1, n):
            data = data << 8
            data = data | bytesRead[i]

        return data

    def restartCpu(self,
                   duId: int) -> None:
        """
        Restart the CPU and set the PC to the first breakpoint.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to restart.
        """
        if not self.isCPUReset(duId):
            self.resetCPU(duId)
        if not self.isCPUHalted(duId):
            self.haltCPU(duId)
        assert self.getPc(duId) == 0

        self.resumeCPU(duId)

        # Depending on the DU configuration, the CPU may halt one clock cycle after
        # reaching the breakpoint. In this case, the CPU may be halted one instruction later.
        assert ((self.getPc(duId) == self.__breakpoints[0]) | (
            self.getPc(duId) == (self.__breakpoints[0] + 4))),  f"Actual PC is {hex(self.getPc(0))}"

    def configureCpu(self,
                     duId: int,
                     breakpoints: list[int],
                     triggerpoints: list[int]) -> None:
        """
        Configure the CPU with the specified breakpoints and triggerpoints.

        Parameters
        ----------
        `duId`: int
            CPU's debug unit ID to configure.
        `breakpoints`: list[int]
            List of breakpoints to set.
        `triggerpoints`: list[int]
            List of triggerpoints to set.
        """
        if not self.isCPUReset(duId):
            self.resetCPU(duId)
        if not self.isCPUHalted(duId):
            self.haltCPU(duId)

        self.removeBreakPoints(duId)
        self.removeTriggerPoints(duId)
        self.setBreakPoints(duId, breakpoints)
        self.setTriggerPoints(duId, triggerpoints)
