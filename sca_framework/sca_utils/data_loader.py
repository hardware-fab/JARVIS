"""
Authors : 
    Andrea Galimberti (andrea.galimberti@polimi.it),
    Davide Galli (davide.galli@polimi.it),
    Davide Zoni (davide.zoni@polimi.it)
"""

import multiprocessing as mp
from multiprocessing.connection import Connection


class PipeDataLoader:
    """
    A class used to load data in a separate process and communicate the data back using a pipe.

    Methods
    -------
    `close()`
        Joins the child process and closes the receiving end of the pipe.
    `receive()`
        Receives data from the pipe. If the pipe is closed, it closes the PipeDataLoader and raises an EOFError.
    """

    def __init__(self,
                 dataLoader: callable,
                 *dataLoaderArgs: list,
                 **dataLoaderKwargs: dict
                 ):
        """
        Initializes the PipeDataLoader with the data loading function and its arguments.

        Parameters
        ----------
        `dataLoader` : callable
            The function to load the data, must return an iterator.
        `*dataLoaderArgs` : list
            The positional arguments for the data loading function.
        `**dataLoaderKwargs` : dict
            The keyword arguments for the data loading function.
        """
        self._rcv, self._snd = mp.Pipe(duplex=False)
        self._child = mp.Process(
            target=PipeDataLoader._dataLoader,
            args=dataLoaderArgs,
            kwargs={'pipe': self._snd, 'load_data_func': dataLoader, **dataLoaderKwargs})
        self._child.start()
        self._snd.close()

    def __del__(self):
        """
        Ensures the child process is joined and the receiving end 
        of the pipe is closed when the PipeDataLoader is deleted.
        """
        self.close()

    def close(self):
        """
        Joins the child process and closes the receiving end of the pipe.
        """
        if self._child.is_alive():
            self._child.join()
        self._rcv.close()

    def receive(self):
        """
        Receives data from the pipe.
        If the pipe is closed, it closes the PipeDataLoader and raises an EOFError.

        Returns
        -------
        The data received from the pipe.

        Raises
        ------
        `EOFError`:
            If the pipe is closed.
        """
        try:
            return self._rcv.recv()
        except EOFError:
            self.close()
            raise

    @staticmethod
    def _dataLoader(*args, **kwargs):
        """
        A function to load data in a separate process and communicate the data back using a pipe.
        """
        pipe: Connection = kwargs.pop('pipe')
        load_data_func: callable = kwargs.pop('load_data_func')

        # Call the provided function with the pipe and any additional arguments
        for data in load_data_func(*args, **kwargs):
            # Send the data through the pipe
            pipe.send(data)
