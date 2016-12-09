import sys
from queue import Queue
from threading import Thread

import pytest

from tornado import ioloop

from gremlin_python.driver.driver_remote_connection import (
    DriverRemoteConnection)
from gremlin_python.structure.graph import Graph


skip = False
try:
    connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
    connection.close()
except:
    skip = True


@pytest.mark.skipif(skip, reason='Gremlin Server is not running')
class TestDriverRemoteConnectionThreaded:

    def test_threaded_client(self):
        q = Queue()
        # Here if we give each thread its own loop there is no problem.
        loop1 = ioloop.IOLoop()
        loop2 = ioloop.IOLoop()
        child = Thread(target=self._executor, args=(q, loop1))
        child2 = Thread(target=self._executor, args=(q, loop2))
        child.start()
        child2.start()
        for x in range(2):
            success = q.get()
            assert success == 'success!'
        child.join()
        child2.join()

    def test_threaded_client_error(self):
        q = Queue()
        # This scenario fails because both threads try to access the main
        # thread event loop - bad - each thread needs its own loop.
        # This is what happens when you can't manually set the loop.
        child = Thread(target=self._executor, args=(q, None))
        child2 = Thread(target=self._executor, args=(q, None))
        child.start()
        child2.start()
        with pytest.raises(RuntimeError):
            try:
                for x in range(2):
                    exc = q.get()
                    if issubclass(exc, Exception):
                        raise exc()
            finally:
                child.join()
                child2.join()

    def _executor(self, q, loop):
        try:
            connection = DriverRemoteConnection(
                'ws://localhost:8182/gremlin', 'g', loop=loop)
            g = Graph().traversal().withRemote(connection)
            assert len(g.V().toList()) == 6
        except:
            q.put(sys.exc_info()[0])
        else:
            q.put('success!')
            connection.close()
