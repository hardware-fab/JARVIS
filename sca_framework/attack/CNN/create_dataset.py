"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

import os
from matplotlib import pyplot as plt
from npy_append_array import NpyAppendArray
import numpy as np
from tqdm.auto import tqdm

from .utils.utils import preprocess
from io_dat.traces_bin import TracesBin
from sca_utils import MeanVarOnline, highpass, norm
from ciphers import AesSca


def _dataLoader(traces_files):
    for trace_file in traces_files:
        trace_bin = TracesBin(trace_file)
        traces, plains = trace_bin.getAllTraces()
        key = trace_bin.getKey()

        yield traces, plains, key

def _computeTargets(plains, key):
    targets = [AesSca.attackedIntermediate(
        plains, key, byte) for byte in range(16)]
    return np.array(targets).T

def _shuffle(all_traces, all_plains, all_targets):
    indices = np.arange(len(all_traces))
    np.random.shuffle(indices)

    all_traces = all_traces[indices]
    all_targets = all_targets[indices]
    all_plains = all_plains[indices]
    return all_traces,all_plains,all_targets

def _computeStd(trace_files, filter):
    mean_var = MeanVarOnline()
    for trace_file in tqdm(trace_files, desc="Computing std"):
        all_traces, _ = TracesBin(trace_file).getAllTraces()
        if filter:
            all_traces = highpass(all_traces)
        mean_var.update(all_traces)
    _, mean, var = mean_var.finalize()
    return mean, var


def _writeConfig(dataset_folder,
                 train_shape,
                 valid_shape,
                 test_shape,
                 window,
                 filter,
                 aggregate_n_samples,
                 std):
    with open(dataset_folder + "config.txt", "w") as file:
        file.write(f"N. training traces: {train_shape[0]}\n")
        file.write(f"N. validation traces: {valid_shape[0]}\n")
        file.write(f"N. test traces: {test_shape[0]}\n")
        file.write(f"N. input samples: {train_shape[1]}\n")
        file.write(f"Filter: {filter}\n")
        file.write(f"Std: {std}\n")
        file.write(f"Window: {window}\n")
        file.write(f"Aggregation: {aggregate_n_samples}\n")


def createDataset(traces_files: list[str],
                  dataset_folder: str,
                  window: list[int] = [],
                  filter: bool = True,
                  aggregate_n_samples: int = 1,
                  std: bool = False,
                  split_traces: float = 0.8) -> None:
    """
    Create a dataset from a list of traces files.

    Parameters
    ----------
    `traces_files` : list[str]
        Traces file pathes to use to create the dataset in .dat format.
        Should be 256, one for each key byte value.
    `dataset_folder` : str
        The folder where the dataset will be stored.
    `window` : list[int], optional
        The window to use to extract the traces. If empty the window will be the whole trace (default is []).
    `filter` : bool, optional
        Apply a highpass filter to traces as preprocessing (default is True).
    `aggregate_n_samples`: int, optional
        How many consecutive samples avarage together as preprocessing (default is 1).
    `std` : bool, optional
        Normalize the traces feature-wise (default is False).
    `split_traces` : float, optional
        The proportion of traces to use for training (default is 0.8).
    """

    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)

    if window == []:
        # The first 50 samples are always before the trigger, i.e. useless
        window = [50, TracesBin(traces_files[0]).getNSamples()]

    if std:
        mean, var = _computeStd(traces_files, filter)
    else:
        mean, var = 0, 1

    train_win_path = os.path.join(dataset_folder, 'train_windows.npy')
    train_tar_path = os.path.join(dataset_folder, 'train_targets.npy')
    train_meta_path = os.path.join(dataset_folder, 'train_meta.npy')
    valid_win_path = os.path.join(dataset_folder, 'valid_windows.npy')
    valid_tar_path = os.path.join(dataset_folder, 'valid_targets.npy')
    valid_meta_path = os.path.join(dataset_folder, 'valid_meta.npy')
    test_win_path = os.path.join(dataset_folder, 'test_windows.npy')
    test_tar_path = os.path.join(dataset_folder, 'test_targets.npy')
    test_meta_path = os.path.join(dataset_folder, 'test_meta.npy')

    with NpyAppendArray(train_win_path, delete_if_exists=True) as npa_train_win, \
            NpyAppendArray(train_tar_path, delete_if_exists=True) as npa_train_tar,  \
            NpyAppendArray(train_meta_path, delete_if_exists=True) as npa_train_meta, \
            NpyAppendArray(valid_win_path, delete_if_exists=True) as npa_valid_win,  \
            NpyAppendArray(valid_tar_path, delete_if_exists=True) as npa_valid_tar,  \
            NpyAppendArray(valid_meta_path, delete_if_exists=True) as npa_valid_meta, \
            NpyAppendArray(test_win_path, delete_if_exists=True) as npa_test_win,    \
            NpyAppendArray(test_tar_path, delete_if_exists=True) as npa_test_tar,    \
            NpyAppendArray(test_meta_path, delete_if_exists=True) as npa_test_meta:

        dataLoader = _dataLoader(traces_files)
        for all_traces, all_plains, key in tqdm(dataLoader, desc="Creating dataset", total=len(traces_files)):
            
            n_traces = len(all_traces)

            n_train_traces = round(n_traces*split_traces)
            n_valid_traces = round(n_traces*(1-split_traces)/2)
            n_test_traces = n_traces - n_train_traces - n_valid_traces

            all_targets = _computeTargets(all_plains, key)

            # Randomize dataset
            all_traces, all_plains, all_targets = _shuffle(all_traces, all_plains, all_targets)

            all_traces = preprocess(
                all_traces, filter, (mean, var), window, aggregate_n_samples)

            # Training
            train_windows = all_traces[:n_train_traces]
            targets = all_targets[:n_train_traces]
            plains = all_plains[:n_train_traces]

            npa_train_win.append(train_windows)
            npa_train_tar.append(targets)
            npa_train_meta.append(
                np.stack((plains, np.broadcast_to(key, (n_train_traces, 16))), axis=1))

            # Validation
            valid_windows = all_traces[n_train_traces:n_train_traces+n_valid_traces]
            targets = all_targets[n_train_traces:n_train_traces+n_valid_traces]
            plains = all_plains[n_train_traces:n_train_traces+n_valid_traces]

            npa_valid_win.append(valid_windows)
            npa_valid_tar.append(targets)
            npa_valid_meta.append(
                np.stack((plains, np.broadcast_to(key, (n_valid_traces, 16))), axis=1))

            # Test
            test_windows = all_traces[n_train_traces+n_valid_traces:]
            targets = all_targets[n_train_traces+n_valid_traces:]
            plains = all_plains[n_train_traces+n_valid_traces:]

            npa_test_win.append(test_windows)
            npa_test_tar.append(targets)
            npa_test_meta.append(
                np.stack((plains, np.broadcast_to(key, (n_test_traces, 16))), axis=1))
    
    _writeConfig(dataset_folder,
                 np.load(train_win_path, mmap_mode='r').shape,
                 np.load(valid_win_path, mmap_mode='r').shape,
                 np.load(test_win_path, mmap_mode='r').shape,
                 window,
                 filter,
                 aggregate_n_samples,
                 std)


def plotTargetStatistics(dataset_folder: str) -> None:
    """
    Plot the distribution of the targets in the dataset and save the plot in `dataset_folder`.
    The three datasets should have the same distribution.

    Parameters
    ----------
    `dataset_folder` : str
        The folder where the dataset is stored.
    """
    train_tar_path = os.path.join(dataset_folder, 'train_targets.npy')
    valid_tar_path = os.path.join(dataset_folder, 'valid_targets.npy')
    test_tar_path = os.path.join(dataset_folder, 'test_targets.npy')

    train_targets = np.load(train_tar_path, mmap_mode='r')
    train_stats = np.unique(train_targets, return_counts=True)
    valid_targets = np.load(valid_tar_path, mmap_mode='r')
    valid_stats = np.unique(valid_targets, return_counts=True)
    test_targets = np.load(test_tar_path, mmap_mode='r')
    test_stats = np.unique(test_targets, return_counts=True)

    plt.figure(figsize=(9, 4))
    ax = plt.subplot(1, 3, 1)
    ax.hist(norm(train_stats[1]), bins=int(180/5))
    ax.set_title("Train")

    ax = plt.subplot(1, 3, 2)
    ax.hist(norm(valid_stats[1]), bins=int(180/5))
    ax.set_title("Validation")

    ax = plt.subplot(1, 3, 3)
    ax.hist(norm(test_stats[1]), bins=int(180/5))
    ax.set_title("Test")

    plt.savefig(os.path.join(dataset_folder,
                'target_statistics.png'), bbox_inches='tight')
    plt.show()
    plt.close()


def printDatasetInfo(dataset_folder: str):
    """
    Print dataset information.

    Parameters
    ----------
    `dataset_folder` : str
        The folder where the dataset is stored.
    """
    config_file = os.path.join(dataset_folder, "config.txt")
    with open(config_file, "r") as file:
        info = file.read()
    print(info)