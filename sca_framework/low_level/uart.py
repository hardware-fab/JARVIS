"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Giuseppe Diceglie
"""

import termios
import serial

DEFAULT_SERIAL_SPEED = termios.B1000000


class Uart():
    def __init__(self, path):
        serial_port = serial.Serial(
            timeout=0.1,
            writeTimeout=2,
            port=path
        )
        if not serial_port.is_open:
            print("Exiting.  Could not open serial port:", serial_port.port)
            exit

        self.__mFd = serial_port
        self.__mBlocking = False
        self.__mBaudRate = DEFAULT_SERIAL_SPEED

        self.__setup()

    def __del__(self):
        self.__mFd.close()

    # def swap(self, other):

    def getBaudRate(self):
        return self.__mBaudRate

    def setBaudRate(self, baud_rate):
        self.__mBaudRate = baud_rate

    def isBlocking(self):
        return self.__mBlocking

    def setBlocking(self, blocking):
        self.__mBlocking = blocking

    def writeBytes(self, bytes_to_write):
        for b in bytes_to_write:
            self.__mFd.write(b.to_bytes(1, 'little'))

    def readBytes(self, n_bytes_to_read):
        data = []
        for i in range(0, n_bytes_to_read):
            data.append(self.__mFd.read()[0])
        return data

    def __setup(self):
        tty = termios.tcgetattr(self.__mFd)
        # iflag
        # disable IGNBRK for mismatched speed tests; otherwise receive break
        # as \000 chars
        tty[0] = tty[0] & ~termios.IGNBRK  # ignore break signal
        # no canonical processing
        tty[0] = tty[0] & ~(termios.IXON | termios.IXOFF |
                            termios.IXANY)  # shut off xon/xoff ctrl

        # oflag
        tty[1] = 0  # no remapping, no delays

        # cflag
        # turn off character processing
        tty[2] = tty[2] & ~termios.CSIZE
        tty[2] = tty[2] | termios.CS8
        # remove parity
        tty[2] = tty[2] & ~(termios.PARENB | termios.PARODD)
        # only one stop bit
        tty[2] = tty[2] & ~termios.CSTOPB
        # disable RTS/CTS hardware flow control
        tty[2] = tty[2] & ~termios.CRTSCTS
        # ignore model control
        # ignore modem controls, enable reading
        tty[2] = tty[2] | (termios.CLOCAL | termios.CREAD)

        # lflag
        tty[3] = 0  # no signaling chars, no echo, no canonical processing

        # ispeed
        tty[4] = self.__mBaudRate

        # ospeed
        tty[5] = self.__mBaudRate

        # cc
        # blocking mode configuration
        tty[6][termios.VMIN] = self.__mBlocking
        tty[6][termios.VTIME] = 5  # 0.5 seconds read timeout

        termios.tcsetattr(self.__mFd, termios.TCSANOW, tty)
