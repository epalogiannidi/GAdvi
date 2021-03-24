import time
from datetime import timedelta


class Timer:
    """ Context manager to count elapsed time
    Usage:
        with Timer() as t:
            y = f(x)
        print(f'Invocation of f took {t.elapsed}s!')
    """

    def __enter__(self):
        """ Enter """
        self._start = time.time()
        return self

    def __exit__(self, *args):
        """ Exit """
        self._end = time.time()
        self._elapsed = self._end - self._start
        self.elapsed = str(timedelta(seconds=self._elapsed))