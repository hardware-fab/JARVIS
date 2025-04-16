"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Giuseppe Diceglie
"""

import ctypes
import os
import numpy as np

FULL_KEY_SIZE = 11*16
LEN = 16

_aes_sbox = (
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16)


class Aes():
    """
    A class used to represent an Aes cipher.
    
    Attributes
    ----------
    `sbox` : np.ndarray
        The Aes sbox.
    `fullKeySize` : int, 176
        The size of the full key of the Aes cipher in bytes.
    `stateSize` : int, 16
        The size of the state of the Aes cipher in bytes.

    Methods
    -------
    `getKey()`:
        Returns the key of the cipher.
    `getPlaintext()`:
        Returns the plaintext of the cipher.
    `computePlaintexts(batch_size)`:
        Compute the first contiguous `batch_size` plaintexts. Run AES_in_place `batch_size` times.
    """
    
    sbox = np.array(_aes_sbox, dtype=np.uint8)
    fullKeySize = FULL_KEY_SIZE
    stateSize = LEN

    def __init__(self,
                 key: int,
                 plaintext: int):
        """
        Initialize a Chiper object.

        Parameters
        ----------
        `key` : int
            The key of the cipher.
        `plaintext` : int
            The plaintext of the cipher.
        """

        self._state_len = Aes.stateSize
        self._full_key_size = Aes.fullKeySize

        libfile = os.path.join(os.path.dirname(
            __file__), "lib/aes.so")
        self._lib = ctypes.CDLL(libfile)

        self._key = key
        self._plaintext = plaintext

        self._c_key = (ctypes.c_uint8 * Aes.stateSize)()
        self._c_key[:] = key.to_bytes(Aes.stateSize, 'big')

        self._c_state = (ctypes.c_uint8 * Aes.stateSize)()
        self._c_state[:] = plaintext.to_bytes(Aes.stateSize, 'big')

        self._c_fullKey = (ctypes.c_uint8 * Aes.fullKeySize)()
        
        self._lib.KeyExpansion(ctypes.byref(self._c_fullKey),
                               ctypes.byref(self._c_key))
        
    def __call__(self) -> int:
        """
        Encrypts the plaintext.
        
        Returns
        ----------
        The ciphertext of the cipher.
        """
        self._encrypt()
        return int.from_bytes(self._c_state[:], 'big')
    
    
    def _encrypt(self):
        self._lib.AES_in_place(ctypes.byref(self._c_fullKey),
                               ctypes.byref(self._c_state))

    def getStateLen(self) -> int:
        """
        Returns the length of the state and key.

        Returns
        ----------
        The length of the state and key.
        """
        return self._state_len

    def getFullKeySize(self) -> int:
        """
        Returns the size of the full key, i.e. the expanded key.

        Returns
        ----------
        The size of the full key.
        """
        return self._full_key_size
    
    def getFullKey(self) -> int:
        """
        Returns the full key of the Clefia cipher, i.e. the expanded key.

        Returns
        ----------
        The full key of the cipher.
        """
        return int.from_bytes(bytes(self._c_fullKey), byteorder='big')

    def getKey(self) -> int:
        """
        Returns the key of the cipher.

        Returns
        ----------
        The key of the cipher.
        """
        return self._key

    def getPlaintext(self) -> int:
        """ 
        Returns the plaintext of the cipher.

        Returns
        ----------
        The plaintext of the cipher.
        """
        return self._plaintext

    def computePlaintexts(self,
                          batch_size: int = 1000) -> list[int]:
        """
        Compute the first contiguous `batch_size` plaintexts.
        Run encryption `batch_size` times.

        Parameters
        ----------
        `batch_size`: int, optional
            Number of cipher cycles to perform (default is 1000).

        Returns
        ----------
        List of `batch_size` contiguous plaintexts.
        """
        # reinitialize the state
        self._c_state[:] = self._plaintext.to_bytes(self._state_len, 'big')

        texts = [0]*batch_size
        for i in range(0, batch_size):
            texts[i] = int.from_bytes(self._c_state[:], 'big')
            self._encrypt()

        return texts
