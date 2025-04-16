"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

from . import Aes
import numpy as np
from typing import Union

class AesSca():
    """
    Side-Channel Analisys class for the Aes cipher.
    
    Methods
    -------
    `attackedSbox(byte)`:
        Return the SBOX used in the cipher based on the byte.
    `attackedKeyByte(key, byte)`:
        Return the byte of the attacked round key based on the byte.
    `attackedPlainsByte(plains, byte)`:
        Return the byte of the attacked plaintext based on the byte.
    `attackedIntermediate(plains, key, byte)`:
        Return the intermediate value used in the attack.
    `invAttackedIntermediate(plains, intermediates, byte)`:
        Return the key value used in the attack for each intermediate.
    `assertByte(byte)`:
        Assert that the target byte is valid.
    """
    
    @staticmethod
    def attackedSbox(byte: int) -> np.ndarray:
        """
        Return the SBOX used in Aes.
        Aes uses the same SBOX for all bytes.
        
        Parameters
        ----------
        `byte` : int, un-used
            Byte of the key to attack.
        
        Returns
        ----------
        The SBOX of precessed by the byte to attack.
        """
        return Aes.sbox
    
    @staticmethod
    def attackedKeyByte(key: Union[bytes, list[int]],
                        byte: int) -> int:
        """
        Return the byte of the attacked round key based on the byte.
        
        Parameters
        ----------
        `key` : bytes | list[int]
            Key to attack.
        `byte` : int
            Byte of the key to attack.
        
        Returns
        ----------
        The byte of the round key to attack.
        """
        return key[byte]
    
    @staticmethod
    def attackedPlainsByte(plains: np.ndarray,
                           byte: int) -> np.ndarray:
        """
        Return the byte of the attacked plaintext based on the byte.
        
        Parameters
        ----------
        `plains` : array_like, shape=(#traces, 16)
            Plaintexts used in the attack.
        `byte` : int
            Byte of the key to attack.
        
        Returns
        ----------
        A numpy array of shape (#traces,) with the plaintext bytes to attack.
        """
        return plains[:, byte]
    
    @staticmethod
    def attackedIntermediate(plains: np.ndarray,
                             key: Union[bytes, list[int]],
                             byte: int) -> np.ndarray:
        """
        Return the intermediate value used in the attack.
        > sbox(plain[byte] ^ key[byte])
        
        Parameters
        ----------
        `plains` : array_like, shape=(#traces, 16)
            Plaintexts used in the attack.
        `key` : bytes | list[int]
            Key to attack.
        `byte` : int
            Byte of the key to attack.
        
        Returns
        ----------
        A numpy array of shape (#traces,) with the intermediate values.
        """
        return Aes.sbox[plains[:, byte] ^ key[byte]]
    
    @staticmethod
    def invAttackedIntermediate(plains: np.ndarray,
                                intermediates: np.ndarray,
                                byte: int) -> np.ndarray:
        """
        Return the key value used in the attack for each intermediate.
        
        Parameters
        ----------
        `plains` : array_like, shape=(#traces, 16)
            Plaintexts used in the attack.
        `intermediates` : array_like, shape=(#traces,)
            Intermediate values guessed in the attack.
        `byte` : int
            Byte of the key to attack.
        
        Returns
        ----------
        A numpy array of shape (#traces,) with the key guesses.
        """
        keys = []
        key_guess = np.arange(0, 256)
        intermediate_guess = Aes.sbox[plains[:, byte, None] ^ key_guess]
        for trace in range(intermediate_guess.shape[0]):
            keys.append(np.where(intermediate_guess[trace] == intermediates[trace])[0])
        return np.array(keys)[:,0]
    
    @staticmethod
    def assertByte(byte: int):
        """
        Assert that the target byte is valid.
        """
        assert 0 <= byte < 16, \
            f"Target byte {byte} invalid: it must be between 0 and 15."
    