"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
    
Other contributor(s):  
    Giuseppe Diceglie
"""

from multiprocessing import Pool
import os

import numpy as np
from scipy.stats import multivariate_normal
from sklearn.decomposition import PCA
from tqdm.auto import tqdm

from io_dat.traces_bin import TracesBin
from sca_utils import *
from ciphers import AesSca

FILE_EXISTS_MSG = "Files already exist:"
ABORTING_MSG = "aborting operation. If you want to override them, set 'force'."
OVERRIDE_MSG = "overriding files..."

PCA_NOT_COMPUTED_MSG = "PCA components and mean not already computed! "\
    + "Compute PCA and then create template."

TEMPLATE_NOT_COMPUTED_MSG = "Template not fitted yet!"\
    + "Fit template and then attack."


def PCA_transform(X, pca_components, pca_mean):
    return (X - pca_mean) @ pca_components.T


def _dataLoader(files: list[str],
                n_traces: int):

    for file in files:
        # Load traces and plaintxt
        traceBin = TracesBin(file)
        traces, plains = traceBin.getTraces(np.arange(n_traces))
        key = TracesBin(file).getKey()

        yield traces, plains, key


class TemplateAttack():
    """
    Template Attack class for AES cipher.

    Methods
    -------
    `computePCA(files, force)`:
        Computes PCA components and saves them into template's folder.
    `fit(files, force)`:
        Computes template's multivariant matrixes and saves them into template's folder.
    `predict(traces, plains)`:
        Attack `traces` using the profiled Template.
    `guessingMetrics(files, n_traces, force)`:
        Computes attack metrics (guessing entropy, guessing distance, and rank)
        averaged over the attacked files and save them. 
    """

    def __init__(self,
                 template_folder: str,
                 n_traces: int = None,
                 mode: str = "sbox",
                 target_byte: int = 0,
                 filter: bool = False,
                 aggregate_n_samples: int = 1,
                 n_principal_comp: int = 10
                 ):
        """
        Parameters
        ----------
        `template_folder`    : str,
            Folder path where to save the template working files.
        `n_traces`           : int, optional
            How many traces use to profile for each key (default uses all traces in file).
        `mode`               : str, optional
            Leakage point on where to perform the attack.
            Choose between: hw(sbox), xor_bit, sbox, xor_byte (default is 'sbox').
        `target_byte`        : int, optional
            Byte of the key to attack (default is 0).
        `filter`             : bool, optional
            Apply a highpass filter to traces as preprocessing (default is False).
        `aggregate_n_samples`: int, optional
            How many consecutive samples avarage together as preprocessing (default is 1).
        `n_principal_comp`   : int, optional
            How many principal components use in PCA (default is 10).

        Raises
        ------
        `AssertionError`
            If `target_byte` is not between 0 and 15.
        """
        AesSca.assertByte(target_byte)

        self._mode = mode
        self.__filter = filter
        self.__n_traces = n_traces
        self.__n_principal_comp = n_principal_comp
        self.__aggregate_n_sample = aggregate_n_samples
        self._byte = target_byte
        self._num_classes = self._getNumClasses()
        self.__template_folder = template_folder
        self._rv_list = None

        model_folder = self.__createFolders(template_folder)

        self.__path_names = {
            "pca_components": model_folder + "pca_components.npy",
            "pca_mean": model_folder + "pca_mean.npy",
            "mean_matrix": model_folder + "mean_matrix.npy",
            "cov_matrix": model_folder + "cov_matrix.npy",
            "ranks": template_folder + "ranks.npy",
            "results": template_folder + "attack_metrics.txt"
        }

        self.__setStatus()
        if self._status == 0:
            self.__writeConfig(template_folder)

    def _getNumClasses(self):
        mode = self._mode
        if mode == "hw(sbox)":
            return 9
        elif mode == "xor_bit":
            return 2
        elif mode == "sbox":
            return 256
        elif mode == "xor_byte":
            return 256
        else:
            raise ValueError(
                f"Unknown mode {mode}. Choose between: hw(sbox), xor_bit, sbox, xor_byte.")

    def _classify(self, plains, key, attack=False):
        plains_byte = AesSca.attackedPlainsByte(plains, self._byte)
        if attack:
            # During attack, key is a possible key value
            # We have to attack for each key value and then guess the correct one
            key_byte = key
        else:
            # During profiling, key is the correct key value made of 16 bytes
            key_byte = key[self._byte]

        mode = self._mode
        sbox = AesSca.attackedSbox(self._byte)
        if mode == "hw(sbox)":
            s = sbox[plains_byte ^ key_byte]
            return hw[s]
        elif mode == "xor_bit":
            xor = plains_byte ^ key_byte
            return xor >> 7
        elif mode == "sbox":
            s = sbox[plains_byte ^ key_byte]
            return s
        elif mode == "xor_byte":
            xor = plains_byte ^ key_byte
            return xor
        else:
            raise ValueError(
                f"Unknown mode {mode}. Choose between: hw(sbox), xor_bit, sbox, xor_byte.")

    def computePCA(self,
                   files: list[str],
                   *,  # Force keyword-only arguments
                   force=False):
        """
        Computes PCA components and saves them into template's folder.

        Parameters
        ----------
        `files` : list[str]
            File pathes containg the profiling traces, in .dat format. Should be 256, one for each key byte value.
        `force`     : bool, optional
            True if you want to override existing files (default is False).
        """
        if self.__checkStatus(1, force):
            return

        TRACE_LENGTH, n_traces = self.__getTraceParameters(files)

        # Create empty data stuctures
        n, sum_, c_, _, _, = self.__initDataStructures(TRACE_LENGTH)

        # Create thread for faster data loading
        pipeLoader = PipeDataLoader(
            _dataLoader, files, n_traces)

        with tqdm(total=len(files), desc="Computing PCA") as pbar:
            while True:
                # Try to receive data from the pipe
                try:
                    traces, plains, key = pipeLoader.receive()
                    traces = self.__preprocess(traces)

                    # Compute intermediate values for PCA
                    class_indexes = self._classify(plains, key)
                    self.__sumPerClass(traces, class_indexes, n, sum_, c_)
                    pbar.update()

                # If the pipe is closed, break the loop
                except EOFError:
                    break

        pca = self.__finalizePCA(n, sum_)
        self.__savePCA(pca)
        self._status = 1

    def fit(self,
            files: list[str],
            *,  # Force keyword-only arguments
            force=False):
        """
        Computes template's multivariant matrixes and saves them into template's folder.

        Parameters
        ----------
        `files` : list[str]
            File pathes containg the profiling traces, in .dat format. 
            Should be 256, one for each key byte value.
        `force`     : bool, optional
            True if you want to override existing files (default is False).
        """
        if self.__checkStatus(2, force):
            return

        _, n_traces = self.__getTraceParameters(files)

        # Create empty data stuctures for Kahan sum
        ndim = np.min([self._num_classes, self.__n_principal_comp])
        n, sum_, c_, sum_sq, c_sq = self.__initDataStructures(ndim)

        # Create thread for faster data loading
        pipeLoader = PipeDataLoader(
            _dataLoader, files, n_traces)

        with tqdm(total=len(files), desc="Fitting template") as pbar:
            while True:
                try:
                    traces, plains, key = pipeLoader.receive()
                    traces = self.__preprocess(traces)
                    traces = PCA_transform(
                        traces, self.__pca_components[:ndim], self.__pca_mean)
                    # Compute intermediate values for template
                    class_indexes = self._classify(plains, key)
                    self.__sumPerClass(
                        traces, class_indexes, n, sum_, c_, sum_sq, c_sq)
                    pbar.update()
                # If the pipe is closed, break the loop
                except EOFError:
                    break

        # Compute covariance and mean matrixes
        cov, mean = self.__finalizeCovMean(
            n, sum_, sum_sq, ndim)
        self.__saveTemplate(cov, mean)
        self._status = 2

    def predict(self,
                traces: np.ndarray,
                plains: np.ndarray) -> np.ndarray:
        """
        Attack `traces` using the profiled Template.
        `traces` and `plains` should match.

        Parameters
        ----------
        `traces`    : array-like
            Traces to attack.
        `plains`     : array-like
            Plaintexts of the corresponding traces to attack.

        Returns
        ----------
        A matrix with log-probabilities for each key and trace.
        """

        N = self.__n_principal_comp

        traces = self.__preprocess(traces)
        traces = PCA_transform(
            traces, self.__pca_components[:N], self.__pca_mean)

        meanMatrix = self.__mean_matrix[:, :N]
        covMatrix = self.__cov_matrix[:, :N, :N]

        # Create one multivariant object for each class
        self.__createRV(meanMatrix, covMatrix)

        n_processes = os.cpu_count() // 2
        batch_size = len(traces) // n_processes + 1

        with Pool(n_processes) as pool:
            args = [(traces[i * batch_size: min((i + 1) * batch_size, len(traces))],
                     plains[i *
                            batch_size: min((i + 1) * batch_size, len(plains))],
                     self) for i in range(n_processes)]
            results = pool.map(TemplateAttack._compute_probabilities, args)

        # Combine results
        P_k = np.vstack(results)

        return P_k

    def guessingMetrics(self,
                        atk_files: list[str],
                        n_traces: int = None,
                        *,
                        force: bool = False
                        ) -> tuple[float, float, np.ndarray]:
        """
        Computes attack metrics (guessing entropy, guessing distance, and rank)
        averaged over the attacked files.
        Rank is a list over the number of traces.

        Parameters
        ----------
        `atk_files` : list[str]
            File pathes containg the attacked traces, in .dat format.
        `n_traces`     : int, optional
            How many traces use to attack for each key (default uses all traces in files).
        `force`        : bool, optional
            True if you want to override existing files (default is False).

        Returns
        ----------
        A tuple like `(guessing-entropy, guessing-distance, rank)`.
        """

        if self.__checkStatus(3, force):
            return float("nan"), float("nan"), np.load(self.__path_names["ranks"])

        ranks = []
        gd = 0

        n_traces = n_traces if n_traces is not None else self.__getTraceParameters(atk_files)[
            1]
        # Create thread for faster data loading
        pipeLoader = PipeDataLoader(
            _dataLoader, atk_files, n_traces)

        with tqdm(total=len(atk_files), desc="Computing metrics", position=0, leave=False) as pbar:
            while True:
                try:
                    traces, plains, key = pipeLoader.receive()
                    # Compute metrics
                    p_k = self.predict(
                        traces[:n_traces], plains[:n_traces])
                    key_byte = AesSca.attackedKeyByte(key, self._byte)
                    ranks_, gd_ = guessMetrics(p_k, key_byte)
                    gd += gd_
                    ranks.append(ranks_)
                    pbar.update()
                # If the pipe is closed, break the loop
                except EOFError:
                    break

        # Average metrics
        gd = gd / len(atk_files)
        ge = guessEntropy(ranks)
        ranks = np.array(ranks)

        dumpMetrics(self.__template_folder, gd, ranks)
        self._status = 3

        return ge, gd, ranks

    def __checkStatus(self, status, force):
        exit = False
        if self._status >= status:
            print(FILE_EXISTS_MSG, end=" ")
            print(ABORTING_MSG) if not force else print(OVERRIDE_MSG)
            exit = True if not force else False
        if status == 2 and self._status == 0:
            print(PCA_NOT_COMPUTED_MSG)
            exit = True
        if status == 3 and self._status < 2:
            print(TEMPLATE_NOT_COMPUTED_MSG)
            exit = True

        if force:
            self._status = status - 1
        return exit

    def __initDataStructures(self, dim):
        n = np.zeros((self._num_classes), dtype="int")
        sum_ = np.zeros((self._num_classes, dim), dtype="float64")
        c_ = np.zeros((self._num_classes, dim), dtype="float64")
        sum_sq = None if self._status == 0 else np.zeros(
            (self._num_classes, dim, dim), dtype="float64")
        c_sq = None if self._status == 0 else np.zeros(
            (self._num_classes, dim, dim), dtype="float64")
        return n, sum_, c_, sum_sq, c_sq,

    def __finalizePCA(self, n, sum_):
        # Ignore warning due to division by 0
        with np.errstate(divide='ignore', invalid='ignore'):
            mean_class = sum_ / n[:, None]
            # Replace NaN elements with 0
            np.nan_to_num(mean_class, copy=False)

        pca = PCA(self._num_classes)
        pca.fit(mean_class)

        return pca

    def __savePCA(self, pca):
        self.__pca_components = pca.components_
        self.__pca_mean = pca.mean_
        np.save(self.__path_names["pca_components"], pca.components_)
        np.save(self.__path_names["pca_mean"], pca.mean_)

    def __finalizeCovMean(self, n, sum_, sum_sq, ndim):
        sum_ = sum_[:, None, :]
        cov = np.zeros((self._num_classes, ndim, ndim))
        mean = np.zeros((self._num_classes, ndim))

        # Ignore warning due to division by 0
        with np.errstate(divide='ignore', invalid='ignore'):
            for j in range(self._num_classes):
                mean[j] = sum_[j] / n[j]
                cov[j] = n[j] * sum_sq[j] - (sum_[j].T @ sum_[j])
            d = n[:, None, None]
            cov = cov / (d * (d - 1))
            # Replace NaN elements with 0
            np.nan_to_num(mean, copy=False)
            np.nan_to_num(cov, copy=False)

        return cov, mean

    def __saveTemplate(self, cov, mean):
        self.__cov_matrix = cov
        self.__mean_matrix = mean
        np.save(self.__path_names["cov_matrix"], cov)
        np.save(self.__path_names["mean_matrix"], mean)

    def __createFolders(self, template_folder):
        if not os.path.exists(template_folder):
            os.mkdir(template_folder)

        model_folder = template_folder + "model/"
        if not os.path.exists(model_folder):
            os.mkdir(model_folder)
        return model_folder

    def __setStatus(self):
        self._status = 0

        if all([
            os.path.isfile(self.__path_names["pca_components"]),
            os.path.isfile(self.__path_names["pca_mean"]),
        ]):
            self._status = 1
            self.__pca_components = np.load(
                self.__path_names["pca_components"])
            self.__pca_mean = np.load(self.__path_names["pca_mean"])

        if all([
            os.path.isfile(self.__path_names["mean_matrix"]),
            os.path.isfile(self.__path_names["cov_matrix"]),
        ]):
            self._status = 2
            self.__mean_matrix = np.load(self.__path_names["mean_matrix"])
            self.__cov_matrix = np.load(self.__path_names["cov_matrix"])

        if all([
            os.path.isfile(self.__path_names["ranks"]),
            os.path.isfile(self.__path_names["results"]),
        ]):
            self._status = 3

    def __writeConfig(self, template_folder):
        with open(template_folder + "config.txt", "w") as file:
            n_traces = "all" if self.__n_traces is None else self.__n_traces
            file.write(f"N. profiling traces: {n_traces}\n")
            file.write(f"Filter: {self.__filter}\n")
            file.write(f"Aggregation: {self.__aggregate_n_sample}\n")
            file.write(f"N. PCA component: {self.__n_principal_comp}\n")
            file.write(f"Mode: {self._mode}\n")
            file.write(f"Target byte: {self._byte}\n")

    def __getTraceParameters(self, files):
        n_traces = self.__n_traces

        traceBin = TracesBin(files[0])
        n_samples = traceBin.getNSamples()
        if n_traces is None:
            n_traces = traceBin.getNTraces()

        return n_samples // self.__aggregate_n_sample, n_traces

    def __preprocess(self, traces):
        if self.__aggregate_n_sample > 1:
            traces = aggregate(traces, self.__aggregate_n_sample)
        if self.__filter:
            traces = highpass(traces)
        return traces

    def __sumPerClass(self, traces, class_indexes, n, sum_, c_, sum_sq=None, c_sq=None):
        for j in np.arange(self._num_classes):
            t_class = traces[class_indexes == j]
            if t_class.shape[0] > 0:
                sum_[j], c_[j] = kahanSum(
                    sum_[j], c_[j], np.sum(t_class, 0, dtype="float64"))
                if self._status == 1:
                    sum_sq[j], c_sq[j] = kahanSum(
                        sum_sq[j], c_sq[j], t_class.T @ t_class)
            n[j] += t_class.shape[0]

    def __createRV(self, meanMatrix, covMatrix):
        if self._rv_list is not None:
            return
        self._rv_list = [
            multivariate_normal(mean, cov, allow_singular=True)
            for mean, cov in zip(meanMatrix, covMatrix)
        ]

    @staticmethod
    def _compute_probabilities(args):
        """
        Perform template attack on a range of traces.

        Parameters:
        --------
        `args` (tuple): A tuple containing the following elements:
            - traces (numpy.ndarray): An array of attack traces.
            - plains (numpy.ndarray): An array of attack plaintexts.
            - instance: An instance of the TemplateAttack class.

        Returns:
        --------
        A 2D array of log-likelihood ratios for each trace and key byte.
        """
        traces, plains, instance = args
        P_k = np.zeros((len(traces), 256))
        for j, at in enumerate(traces):
            for k in range(256):
                class_ = instance._classify(
                    plains[j: j + 1], k, attack=True)[0]
                rv = instance._rv_list[class_]
                p_jk = rv.pdf(at)
                if p_jk != 0:
                    P_k[j, k] = np.log(p_jk)
        return P_k
