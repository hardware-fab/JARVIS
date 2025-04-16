"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

import numpy as np
import pickle
from typing import Union

__hw = [bin(x).count("1") for x in range(256)]

hw = np.array(__hw)


def hammingWeight(n: int) -> int:
    """
    Compute the Hamming weight of an integer (the number of set bits).

    Parameters
    ----------
    n : int
        The integer for which to compute the Hamming weight.

    Returns
    -------
    The Hamming weight of `n`.
    """
    return hw[n & 0xff] + hw[(n >> 8) & 0xff] + hw[(n >> 16) & 0xff] + hw[(n >> 24) & 0xff]


def little2big(integer: int,
               num_bytes: int = None) -> int:
    """
    Convert a little-endian integer into a big-endian integer, or vice versa.

    Parameters
    ----------
    `integer` : int
        The integer to be converted.
    `num_bytes` : int, optional
        The length of the word in bytes.

    Returns
    -------
    The converted integer.
    """

    if num_bytes is None:
        # Compute the number of bytes required
        num_bytes = (integer.bit_length() + 7) // 8
    a = integer.to_bytes(num_bytes, 'little')
    return int.from_bytes(a, 'big')


def kahanSum(sum_: np.ndarray,
             c: np.ndarray,
             element: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Computes the sum of `element` and `sum_`, using the Kahan summation algorithm.

    Parameters
    ----------
    `sum_`    : array_like
        The current running sum.
    `c`       : array_like
        The previous correction term.
    `element` : array_like
        The next element to add.

    Returns
    ----------
    The new running sum and the new correction term.

    Raises
    ------
    `AssertionError`
        If parameters shapes are not equal.
    """

    assert sum_.shape == c.shape, \
        f"sum_ and c shape must be equal: sum_ {sum_.shape}, c {c.shape}"
    assert element.shape == c.shape, \
        f"element and c shape must be equal: element {element.shape}, c {c.shape}"

    y = element - c
    t = sum_ + y
    c = (t - sum_) - y

    sum_ = t

    return sum_, c


def intToBytes(integer: int,
               num_bytes: int = None) -> np.ndarray:
    """
    Convert an integer into a numpy array of bytes.

    Parameters
    ----------
    `integer` : int
        The integer to be converted.
    `num_bytes` : int, optional
        The number of bytes to use for the conversion (default is the minimum number of bytes).

    Returns
    ----------
    A numpy array of unsigned 8-bit integers (dtype=np.uint8) that represents
    the byte arrays of the input integer.
    """

    if num_bytes is None:
        # Compute the number of bytes required
        num_bytes = (integer.bit_length() + 7) // 8
    bytes = list(integer.to_bytes(num_bytes, 'big'))
    return np.array(bytes, dtype=np.uint8)


def bytesToInt(bytes_: Union[bytes, list[int]]) -> int:
    """
    Convert a list of bytes into an integer.

    Parameters
    ----------
    `bytes_` : bytes | list[int8]
        A list of bytes to be converted.

    Returns
    ----------
    An integer that represents the concatenation of the input bytes.
    """

    integer = int.from_bytes(bytes_, byteorder='big')
    return integer


def saveObject(obj: object,
               filename: str):
    """
    Save a Python objet into a pickle file.
    Overwrites any existing file.

    Parameters
    ----------
    `obj` : object
        Object to save.
    `filename` : str
        File path where to save `obj`.
    """
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp, pickle.HIGHEST_PROTOCOL)


def loadObject(filename: str) -> object:
    """
    Load a Python object from a pickle file.
    
    Parameters
    ----------
    `filename` : str
        File path where to load the object from.
    
    Returns
    -------
    The loaded object.
    """
    with open(filename, 'rb') as obj:
        ret_obj = pickle.load(obj)
    return ret_obj

def sortPredictions(predictions: np.ndarray,
                    intermediate_to_key: np.ndarray) -> np.ndarray:
    """
    Sort the output predictions based on the key value.

    Parameters
    ----------
    `predictions` : array_like, shape=(#traces, #guess_values)
        Predictions to sort.
        Predictions are assumed to be ordered by guessed intermediate value.
    `intermediate_to_key`: array_like, shape=(#traces, #guess_values)
        Mapping from guessed intermediate to key.
        For each trace, a key value is associated to each guessed intermediate value. 

    Returns
    --------
    A copy of `predictions` ordered by key value.

    Raises
    ------
    `AssertionError`
        If there is at least one prediction with only zeroes.
    """
    idx = np.argsort(intermediate_to_key)
    key_bytes_proba = predictions[np.arange(predictions.shape[0])[:, None], idx]
    
    if not np.all(key_bytes_proba > 0):
        # We do not want an -inf here, put a very small epsilon
        zero_predictions = key_bytes_proba[key_bytes_proba != 0]
        assert len(zero_predictions) > 0, \
            "Got a prediction with only zeroes... this should not happen!"
        key_bytes_proba[key_bytes_proba == 0] = np.finfo(predictions.dtype).tiny

    return key_bytes_proba
