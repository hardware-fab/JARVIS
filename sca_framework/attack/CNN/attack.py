"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Francesco Lattari
"""

from tqdm.auto import tqdm

import torch
import numpy as np
from math import ceil

from .utils import (parse_arguments, get_neptune_run, preprocess,
                    get_experiment_config_dir)
from sca_utils import *
from ciphers.aesSca import AesSca

import attack.CNN.modules as modules
from io_dat.traces_bin import TracesBin


def _dataLoader(files, filter, std, window, aggregate_n_samples):
    for f in files:
        t_bin = TracesBin(f)
        traces, ptexts = t_bin.getAllTraces()
        key = t_bin.getKey()

        traces = _preprocess(traces, filter, std, window, aggregate_n_samples)

        yield traces, ptexts, key


def _preprocess(traces, filter, std, window, aggregate_n_samples):
    mean, var = (np.mean(traces, axis=0), np.var(
        traces, axis=0)) if std else (0, 1)
    return preprocess(traces, filter, (mean, var), window, aggregate_n_samples)


def _batchify(traces, batch_size):
    n_iters = ceil(traces.shape[0] / batch_size)
    for i in range(n_iters):
        low_plain_idx = i*batch_size
        high_plain_idx = min((i+1)*batch_size, traces.shape[0])
        real_batch_size = high_plain_idx - low_plain_idx

        batch_traces = traces[low_plain_idx: high_plain_idx]
        batch_traces = batch_traces.reshape(real_batch_size, traces.shape[-1])

        yield batch_traces


def _classify(traces, module, device):
    traces = torch.from_numpy(traces)
    traces = traces.to(device)

    with torch.no_grad():
        y_hat = module(traces)
        y_hat = torch.nn.functional.softmax(y_hat, 1)

    return y_hat.detach()


def predict(traces: int,
            module: torch.nn.Module,
            batch_size: int,
            device: torch.device) -> np.ndarray:
    """
    Predict the sbox probabilities for a batch of traces.

    Parameters
    ----------
    `traces` : np.ndarray
        The traces to predict on.
    `module` : torch.nn.Module
        The model to use for the prediction.
    `batch_size` : int
        The batch size to use for the prediction.
    `device` : torch.device
        The device to use for the prediction.
    """
    softmax_preds = []

    for traces_batch in _batchify(traces, batch_size):
        # NORMALIZE
        traces_batch = (traces_batch - np.mean(traces_batch, 1)
                        [:, None]) / np.std(traces_batch, 1)[:, None]

        ret = _classify(traces_batch, module, device)
        softmax_preds.append(ret)

    softmax_preds = torch.cat(softmax_preds, dim=0)

    return softmax_preds.cpu().data.numpy()


def getModule(SID: str,
              neptune_config: str = 'attack/CNN/configs/common/neptune_configs.yaml') -> torch.nn.Module:
    """
    Get the best model from a Neptune Run and return the corresponding module.

    Parameters
    ----------
    `SID` : str
        The Neptune Run ID.
    `neptune_config` : str, optional
        The path to the Neptune configuration file (default is 'attack/CNN/configs/common/neptune_configs.yaml').

    Returns
    ----------
    The best model from the Neptune Run.
    """

    # Get Neptune Run (by SID)
    df = get_neptune_run(neptune_config, SID)

    # Get experiment name
    exp_name = df['sys/name'].iloc[0]

    # Get best model path
    best_model_ckpt = df['experiment/model/best_model_path'].iloc[0]

    # Get config dir
    config_dir = get_experiment_config_dir(best_model_ckpt, exp_name)

    _, module_config, __ = parse_arguments(config_dir)

    # Build Model
    # -----------
    module_name = module_config['module']['name']
    module_config = module_config['module']['config']
    module_class = getattr(modules, module_name)
    module = module_class.load_from_checkpoint(best_model_ckpt,
                                               module_config=module_config)

    return module


def guessingMetrics(atk_files: list[str],
                    module: torch.nn.Module,
                    target_byte: int = 0,
                    window: list[int] = [],
                    filter: bool = True,
                    aggregate_n_samples: int = 1,
                    std: bool = False,
                    batch_size: int = 512,
                    gpu=0
                    ) -> tuple[float, float, np.ndarray]:
    """
    Computes attack metrics (guessing entropy, guessing distance, and rank)
    averaged over the attacked files.
    Rank is a list over the number of traces.

    Parameters
    ----------
    `atk_files` : list[str]
        File pathes containg the attacked traces, in .dat format.
    `module` : modules.SboxClassifier
        The trained model to use for the attack.
    `target_byte` : int, optional
        Byte of the key to attack. To set the same as used during training (default is 0).
    `window` : list[int], optional
        The window to use to extract the traces. If empty the window will be the whole trace.
        To set the same as used during training (default is []).
    `filter` : bool, optional
        Apply a highpass filter to traces as preprocessing.
        To set the same as used during training (default is True).
    `aggregate_n_samples`: int, optional
        How many consecutive samples avarage together as preprocessing.
        To set the same as used during training (default is 1).
    `std` : bool, optional
        Normalize the traces feature-wise
        To set the same as used during training (default is False).
    `batch_size` : int, optional
        The batch size to use for the attack (default is 512).
    `gpu` : int, optional
        The GPU to use for the attack (default is 0).
        0 if you want to use the first GPU, 1 if you want to use the second GPU, and so on

    Returns
    ----------
    A tuple like `(guessing-entropy, guessing-distance, rank)`.
    """

    # Get Device
    device = torch.device(
        f'cuda:{gpu}' if torch.cuda.is_available() else 'cpu')

    # Set Module
    module.to(device)
    module.eval()

    if window == []:
        # The first 50 samples are always before the trigger, i.e. useless
        window = [50, TracesBin(atk_files[0]).getNSamples()]

    # Create thread for faster data loading
    pipeLoader = PipeDataLoader(
        _dataLoader, atk_files, filter, std, window, aggregate_n_samples)

    ranks = []
    gds = []
    with tqdm(total=len(atk_files), desc='Predict key probabilities') as pbar:
        while True:
            try:
                traces, ptexts, key = pipeLoader.receive()

                # Classification
                sbox_proba = predict(
                    traces, module, batch_size, device)
                key_proba = np.zeros((len(sbox_proba), 256))

                for key_byte_guess in range(256):
                    indexes = AesSca.attackedIntermediate(
                        ptexts, [key_byte_guess]*16, target_byte)
                    key_proba[:, key_byte_guess] = sbox_proba[np.arange(
                        len(indexes)), indexes]

                # Metrics
                rank_ak, gd_ak = guessMetrics(
                    np.log(key_proba), key[target_byte])
                ranks.append(rank_ak)
                gds.append(gd_ak)

                pbar.update()
            except EOFError:
                break

    gd = np.mean(gds)
    ge = guessEntropy(ranks)
    ranks = np.array(ranks)

    return ge, gd, ranks
