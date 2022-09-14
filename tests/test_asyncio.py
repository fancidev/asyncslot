from test.test_asyncio.test_base_events import BaseEventLoopTests
from shim import QtCore
from asyncslot._base_events import AsyncSlotBaseEventLoop
from unittest import mock
import unittest


class MyBaseEventLoopTests(BaseEventLoopTests):

    def setUp(self):
        if QtCore.QCoreApplication.instance() is not None:
            self.app = QtCore.QCoreApplication.instance()
        else:
            self.app = QtCore.QCoreApplication([])
        super().setUp()
        self.loop = AsyncSlotBaseEventLoop()
        self.loop._selector = mock.Mock()
        self.loop._selector.select.return_value = ()
        self.set_event_loop(self.loop)

    def tearDown(self):
        super().tearDown()
        self.app = None


if __name__ == "__main__":
    unittest.main()
