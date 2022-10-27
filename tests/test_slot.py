""" test_slot.py - test the asyncslot() function """

import asyncio
import unittest
from shim import QtCore
from qtinter import asyncslot, nocheck, using_asyncio_from_qt


is_pyqt = QtCore.__name__.startswith('PyQt')

if is_pyqt:
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
else:
    Signal = QtCore.Signal
    Slot = QtCore.Slot


called = []


def visit(s, tag=None):
    if tag is not None:
        msg = f'{s}({tag.secret})'
    else:
        msg = s
    # print(msg)
    called.append(msg)


class MySignalObject(QtCore.QObject):
    ready0 = QtCore.Signal()
    ready1 = QtCore.Signal(bool)


qt_slot_supports_descriptor = not QtCore.__name__.startswith('PyQt')


class MySlotMixin:
    secret = 'Cls'

    def __init__(self):
        super().__init__()
        self.secret = 'Self'

    # -------------------------------------------------------------------------
    # Instance method
    # -------------------------------------------------------------------------

    def method(self):
        visit('method', self)

    @QtCore.Slot()
    def slot_method(self):
        visit('slot_method', self)

    async def amethod(self):
        visit('amethod.1', self)
        await asyncio.sleep(0)
        visit('amethod.2', self)

    @QtCore.Slot()
    async def slot_amethod(self):
        visit('slot_amethod.1', self)
        await asyncio.sleep(0)
        visit('slot_amethod.2', self)

    @asyncslot
    async def decorated_amethod(self):
        visit('decorated_amethod.1', self)
        await asyncio.sleep(0)
        visit('decorated_amethod.2', self)

    @QtCore.Slot()
    @asyncslot
    async def slot_decorated_amethod(self):
        visit('slot_decorated_amethod.1', self)
        await asyncio.sleep(0)
        visit('slot_decorated_amethod.2', self)

    @asyncslot
    @QtCore.Slot()
    async def decorated_slot_amethod(self):
        visit('decorated_slot_amethod.1', self)
        await asyncio.sleep(0)
        visit('decorated_slot_amethod.2', self)

    # -------------------------------------------------------------------------
    # Class method
    # -------------------------------------------------------------------------

    @classmethod
    def class_method(cls):
        visit('class_method', cls)

    @classmethod
    async def class_amethod(cls):
        visit('class_amethod.1', cls)
        await asyncio.sleep(0)
        visit('class_amethod.2', cls)

    @classmethod
    @asyncslot
    async def class_decorated_amethod(cls):
        visit('class_decorated_amethod.1', cls)
        await asyncio.sleep(0)
        visit('class_decorated_amethod.2', cls)

    # Not supported
    # @asyncslot
    # @classmethod
    # async def class_decorated_amethod(cls):
    #     visit('class_decorated_amethod.1', cls)
    #     await asyncio.sleep(0)
    #     visit('class_decorated_amethod.2', cls)

    if qt_slot_supports_descriptor:

        @QtCore.Slot()
        @classmethod
        def slot_class_method(cls):
            visit('slot_class_method', cls)

        @classmethod
        @QtCore.Slot()
        def class_slot_method(cls):
            visit('class_slot_method', cls)

    # -------------------------------------------------------------------------
    # Static method
    # -------------------------------------------------------------------------

    @staticmethod
    def static_method():
        visit('static_method')

    @staticmethod
    async def static_amethod():
        visit('static_amethod.1')
        await asyncio.sleep(0)
        visit('static_amethod.2')

    @staticmethod
    @asyncslot
    async def static_decorated_amethod():
        visit('static_decorated_amethod.1')
        await asyncio.sleep(0)
        visit('static_decorated_amethod.2')

    if qt_slot_supports_descriptor:

        @QtCore.Slot()
        @staticmethod
        def slot_static_method():
            visit('slot_static_method')

        @staticmethod
        @QtCore.Slot()
        def static_slot_method():
            visit('static_slot_method')


class MySlotObject(MySlotMixin, QtCore.QObject):
    pass


def func():
    visit('func')


@QtCore.Slot()
def slot_func():
    visit('slot_func')


async def afunc():
    visit('afunc.1')
    await asyncio.sleep(0)
    visit('afunc.2')


@asyncslot
async def decorated_afunc():
    visit('decorated_afunc.1')
    await asyncio.sleep(0)
    visit('decorated_afunc.2')


@QtCore.Slot()
async def slot_afunc():
    visit('slot_afunc.1')
    await asyncio.sleep(0)
    visit('slot_afunc.2')


@QtCore.Slot()
@asyncslot
async def slot_decorated_afunc():
    visit('slot_decorated_afunc.1')
    await asyncio.sleep(0)
    visit('slot_decorated_afunc.2')


@asyncslot
@QtCore.Slot()
async def decorated_slot_afunc():
    visit('decorated_slot_afunc.1')
    await asyncio.sleep(0)
    visit('decorated_slot_afunc.2')


qc = QtCore.Qt.ConnectionType.QueuedConnection


class TestSlotOnFreeFunction(unittest.TestCase):
    # Tests for asyncslot wrapping or decorating free function.

    def setUp(self) -> None:
        if QtCore.QCoreApplication.instance() is not None:
            self.app = QtCore.QCoreApplication.instance()
        else:
            self.app = QtCore.QCoreApplication([])

        self.qt_loop = QtCore.QEventLoop()
        self.sender = MySignalObject()
        self.signal = self.sender.ready1
        self.connection = None

    def tearDown(self) -> None:
        if self.connection is not None:
            self.signal.disconnect()
            self.connection = None
        self.sender = None
        self.qt_loop = None
        self.app = None

    def _run_once(self):
        QtCore.QTimer.singleShot(0, self.qt_loop.quit)
        self.signal.emit(True)

        called.clear()
        with using_asyncio_from_qt():
            if hasattr(self.qt_loop, 'exec'):
                self.qt_loop.exec()
            else:
                self.qt_loop.exec_()
        return called.copy()

    # -------------------------------------------------------------------------
    # Test non-async free function without Qt.Slot decoration
    # -------------------------------------------------------------------------

    def test_func(self):
        # Qt sanity check
        self.connection = self.signal.connect(func, qc)
        result = self._run_once()
        self.assertEqual(result, ['func'])

    def test_wrapped_func(self):
        # Wrapping a func is an error
        with self.assertRaises(TypeError):
            asyncslot(func)

    def test_decorated_func(self):
        # Decorating a func is an error
        with self.assertRaises(TypeError):
            @asyncslot
            def fn():
                pass

    # -------------------------------------------------------------------------
    # Test non-async free function with Qt.Slot decoration
    # -------------------------------------------------------------------------

    def test_slot_func(self):
        # Qt sanity check
        self.connection = self.signal.connect(slot_func, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_func'])

    def test_wrapped_slot_func(self):
        # Wrapping a func is an error
        with self.assertRaises(TypeError):
            asyncslot(slot_func)

    def test_decorated_slot_func(self):
        # Decorating a func is an error
        with self.assertRaises(TypeError):
            @asyncslot
            @QtCore.Slot()
            def fn():
                pass

    # -------------------------------------------------------------------------
    # Test async free function without Qt.Slot decoration
    # -------------------------------------------------------------------------

    def test_wrapped_afunc(self):
        # Test wrapping afunc
        self.connection = self.signal.connect(asyncslot(afunc), qc)
        result = self._run_once()
        self.assertEqual(result, ['afunc.1', 'afunc.2'])

    def test_decorated_afunc(self):
        # Test decorating afunc
        self.connection = self.signal.connect(decorated_afunc, qc)
        result = self._run_once()
        self.assertEqual(result, ['decorated_afunc.1', 'decorated_afunc.2'])

    def test_wrapped_decorated_afunc(self):
        # Wrapping a decorated afunc is an error
        with self.assertRaises(TypeError):
            asyncslot(decorated_afunc)

    # -------------------------------------------------------------------------
    # Test async free function with Qt.Slot decoration
    # -------------------------------------------------------------------------

    def test_wrapped_slot_afunc(self):
        # Test wrapping slot_afunc
        self.connection = self.signal.connect(asyncslot(slot_afunc), qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_afunc.1', 'slot_afunc.2'])

    def test_decorated_slot_afunc(self):
        self.connection = self.signal.connect(decorated_slot_afunc, qc)
        result = self._run_once()
        self.assertEqual(result, ['decorated_slot_afunc.1',
                                  'decorated_slot_afunc.2'])

    def test_slot_decorated_afunc(self):
        self.connection = self.signal.connect(slot_decorated_afunc, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_decorated_afunc.1',
                                  'slot_decorated_afunc.2'])

    # -------------------------------------------------------------------------
    # Test wrapped free function that's not apparently a coroutine function
    # -------------------------------------------------------------------------

    def test_wrapped_afunc_indirect(self):
        with self.assertRaises(TypeError):
            asyncslot(lambda: afunc())

        self.connection = self.signal.connect(
            asyncslot(nocheck(lambda: afunc())), qc)
        result = self._run_once()
        self.assertEqual(result, ['afunc.1', 'afunc.2'])


class TestSlotOnQObject(unittest.TestCase):

    def setUp(self) -> None:
        if QtCore.QCoreApplication.instance() is not None:
            self.app = QtCore.QCoreApplication.instance()
        else:
            self.app = QtCore.QCoreApplication([])

        self.qt_loop = QtCore.QEventLoop()
        self.receiver = MySlotObject()
        self.sender = MySignalObject()
        self.signal = self.sender.ready1
        self.connection = None

    def tearDown(self) -> None:
        if self.connection is not None:
            self.signal.disconnect()
            self.connection = None
        self.sender = None
        self.receiver = None
        self.qt_loop = None
        self.app = None

    def _run_once(self):
        QtCore.QTimer.singleShot(0, self.qt_loop.quit)
        self.signal.emit(True)

        called.clear()
        with using_asyncio_from_qt():
            if hasattr(self.qt_loop, 'exec'):
                self.qt_loop.exec()
            else:
                self.qt_loop.exec_()
        return called.copy()

    # -------------------------------------------------------------------------
    # Test non-async method
    # -------------------------------------------------------------------------

    def test_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(self.receiver.method, qc)
        result = self._run_once()
        self.assertEqual(result, ['method(Self)'])

    def test_wrapped_method(self):
        # Wrapping a method is an error
        with self.assertRaises(TypeError):
            asyncslot(self.receiver.method)

    def test_slot_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(self.receiver.slot_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_method(Self)'])

    def test_wrapped_slot_method(self):
        # Wrapping a method is an error
        with self.assertRaises(TypeError):
            asyncslot(self.receiver.slot_method)

    # -------------------------------------------------------------------------
    # Test async method
    # -------------------------------------------------------------------------

    def test_wrapped_amethod(self):
        self.connection = self.signal.connect(
            asyncslot(self.receiver.amethod), qc)
        result = self._run_once()
        self.assertEqual(result, ['amethod.1(Self)', 'amethod.2(Self)'])

    def test_decorated_amethod(self):
        self.connection = self.signal.connect(
            self.receiver.decorated_amethod, qc)
        result = self._run_once()
        self.assertEqual(result, ['decorated_amethod.1(Self)',
                                  'decorated_amethod.2(Self)'])

    def test_wrapped_decorated_amethod(self):
        with self.assertRaises(TypeError):
            asyncslot(self.receiver.decorated_amethod)

    def test_wrapped_slot_amethod(self):
        self.connection = self.signal.connect(
            asyncslot(self.receiver.slot_amethod), qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_amethod.1(Self)',
                                  'slot_amethod.2(Self)'])

    def test_decorated_slot_amethod(self):
        self.connection = self.signal.connect(
            self.receiver.decorated_slot_amethod, qc)
        result = self._run_once()
        self.assertEqual(result, ['decorated_slot_amethod.1(Self)',
                                  'decorated_slot_amethod.2(Self)'])

    def test_slot_decorated_amethod(self):
        self.connection = self.signal.connect(
            self.receiver.slot_decorated_amethod, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_decorated_amethod.1(Self)',
                                  'slot_decorated_amethod.2(Self)'])

    # -------------------------------------------------------------------------
    # Test non-async class method
    # -------------------------------------------------------------------------

    def test_class_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(self.receiver.class_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['class_method(Cls)'])

    def test_wrapped_class_method(self):
        with self.assertRaises(TypeError):
            asyncslot(self.receiver.class_method)

    @unittest.skipUnless(qt_slot_supports_descriptor, 'not supported by PyQt')
    def test_slot_class_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(
            self.receiver.slot_class_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_class_method(Cls)'])

    @unittest.skipUnless(qt_slot_supports_descriptor, 'not supported by PyQt')
    def test_class_slot_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(
            self.receiver.class_slot_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['class_slot_method(Cls)'])

    # -------------------------------------------------------------------------
    # Test async class method
    # -------------------------------------------------------------------------

    def test_wrapped_class_amethod(self):
        self.connection = self.signal.connect(
            asyncslot(self.receiver.class_amethod), qc)
        result = self._run_once()
        self.assertEqual(result, ['class_amethod.1(Cls)',
                                  'class_amethod.2(Cls)'])

    def test_class_decorated_amethod(self):
        self.connection = self.signal.connect(
            self.receiver.class_decorated_amethod, qc)
        result = self._run_once()
        self.assertEqual(result, ['class_decorated_amethod.1(Cls)',
                                  'class_decorated_amethod.2(Cls)'])

    # -------------------------------------------------------------------------
    # Test non-async static method
    # -------------------------------------------------------------------------

    def test_static_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(self.receiver.static_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['static_method'])

    def test_wrapped_static_method(self):
        with self.assertRaises(TypeError):
            asyncslot(self.receiver.static_method)

    @unittest.skipUnless(qt_slot_supports_descriptor, 'not supported by PyQt')
    def test_slot_static_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(
            self.receiver.slot_static_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['slot_static_method'])

    @unittest.skipUnless(qt_slot_supports_descriptor, 'not supported by PyQt')
    def test_static_slot_method(self):
        # Qt sanity check
        self.connection = self.signal.connect(
            self.receiver.static_slot_method, qc)
        result = self._run_once()
        self.assertEqual(result, ['static_slot_method'])

    # -------------------------------------------------------------------------
    # Test async static method
    # -------------------------------------------------------------------------

    def test_wrapped_static_amethod(self):
        self.connection = self.signal.connect(
            asyncslot(self.receiver.static_amethod), qc)
        result = self._run_once()
        self.assertEqual(result, ['static_amethod.1', 'static_amethod.2'])

    def test_static_decorated_amethod(self):
        self.connection = self.signal.connect(
            self.receiver.static_decorated_amethod, qc)
        result = self._run_once()
        self.assertEqual(result, ['static_decorated_amethod.1',
                                  'static_decorated_amethod.2'])


class TestSlotOnNonQObject(TestSlotOnQObject):
    def setUp(self) -> None:
        super().setUp()
        self.receiver = MySlotMixin()

    @unittest.skipIf(is_pyqt, "not supported by PyQt")
    def test_slot_method(self):
        super().test_slot_method()

    @unittest.skipIf(is_pyqt, "not supported by PyQt")
    def test_slot_decorated_amethod(self):
        super().test_slot_decorated_amethod()

    @unittest.skipIf(is_pyqt, "not supported by PyQt")
    def test_decorated_slot_amethod(self):
        super().test_decorated_slot_amethod()


class Sender(QtCore.QObject):
    if hasattr(QtCore, "pyqtSignal"):
        signal = QtCore.pyqtSignal(int)
    else:
        signal = QtCore.Signal(int)


class Receiver:
    def __init__(self, output):
        self.output = output

    async def original_slot(self, v):
        self.output[0] += v

    @asyncslot
    async def decorated_slot(self, v):
        self.output[0] *= v


class StrongReceiver:
    __slots__ = 'output',

    def __init__(self, output):
        self.output = output

    def method(self, v):
        self.output[0] -= v

    async def amethod(self, v):
        self.output[0] += v

    @asyncslot
    async def decorated_amethod(self, v):
        self.output[0] *= v


class TestSlotLifetime(unittest.TestCase):

    def setUp(self) -> None:
        if QtCore.QCoreApplication.instance() is not None:
            self.app = QtCore.QCoreApplication.instance()
        else:
            self.app = QtCore.QCoreApplication([])

    def tearDown(self) -> None:
        self.app = None

    def test_weak_reference_decorated(self):
        # Connection with bounded decorated method holds weak reference.
        output = [1]
        sender = Sender()
        receiver = Receiver(output)
        with using_asyncio_from_qt():
            sender.signal.connect(receiver.decorated_slot)
            sender.signal.emit(3)
            self.assertEqual(output[0], 3)
            receiver = None
            sender.signal.emit(5)
            # expecting no change, because connection should have been deleted
            self.assertEqual(output[0], 3)

    def test_weak_reference_wrapped(self):
        # Wrapping a bounded method holds strong reference to the receiver
        # object.
        output = [1]
        sender = Sender()
        receiver = Receiver(output)
        with using_asyncio_from_qt():
            sender.signal.connect(asyncslot(receiver.original_slot))
            sender.signal.emit(3)
            self.assertEqual(output[0], 4)
            receiver = None
            sender.signal.emit(5)
            # expecting change, because connection is still alive
            self.assertEqual(output[0], 4)

    def test_weak_reference_wrapped_2(self):
        # Keeping a (strong) reference to wrapped asyncslot keeps the
        # underlying method alive (similar to keeping a strong reference
        # to the underlying method).
        output = [1]
        sender = Sender()
        receiver = Receiver(output)
        with using_asyncio_from_qt():
            the_slot = asyncslot(receiver.original_slot)
            sender.signal.connect(the_slot)
            # TODO: test disconnect(the_slot)
            sender.signal.emit(3)
            self.assertEqual(output[0], 4)
            receiver = None
            sender.signal.emit(5)
            # The slot should still be invoked because the_slot keeps it alive.
            self.assertEqual(output[0], 9)
            the_slot = None
            sender.signal.emit(6)
            # The slot should no longer be called
            self.assertEqual(output[0], 9)

    def test_strong_reference(self):
        # Wrapping a method in partial keeps the receiver object alive.
        # This test also tests that functools.partial() is supported.
        import functools

        output = [1]
        sender = Sender()
        receiver = Receiver(output)
        with using_asyncio_from_qt():
            sender.signal.connect(
                asyncslot(functools.partial(receiver.original_slot)))
            sender.signal.emit(3)
            self.assertEqual(output[0], 4)
            receiver = None
            sender.signal.emit(5)
            # expecting change, because connection is still alive
            self.assertEqual(output[0], 9)

    def test_await(self):
        # asyncslot returns a Task object and so can be awaited.

        counter = 0

        @asyncslot
        async def work():
            await asyncio.sleep(0.1)
            return 1

        async def entry():
            nonlocal counter
            for _ in range(5):
                await work()
                counter += 1
            loop.quit()

        QtCore.QTimer.singleShot(0, asyncslot(entry))

        with using_asyncio_from_qt():
            loop = QtCore.QEventLoop()
            if hasattr(loop, 'exec'):
                loop.exec()
            else:
                loop.exec_()

        self.assertEqual(counter, 5)

    def test_strong_receiver(self):
        # Test connecting to a bounded method of an object that does not
        # support weak reference.
        output = [1]
        sender = Sender()
        receiver = StrongReceiver(output)
        with using_asyncio_from_qt():
            with self.assertRaises(SystemError if is_pyqt else TypeError):
                sender.signal.connect(receiver.method)
            with self.assertRaises(SystemError if is_pyqt else TypeError):
                sender.signal.connect(receiver.decorated_amethod)
            with self.assertRaises(TypeError):
                sender.signal.connect(asyncslot(receiver.amethod))


class Control(QtCore.QObject):
    valueChanged = Signal((int,), (str,))


class Widget(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self.control1 = Control(self)
        self.control1.setObjectName("control1")
        self.control2 = Control(self)
        self.control2.setObjectName("control2")
        self.control3 = Control(self)
        self.control3.setObjectName("control3")
        self.control4 = Control(self)
        self.control4.setObjectName("control4")
        self.metaObject().connectSlotsByName(self)
        self.values = []

    def on_control1_valueChanged(self, newValue):
        self.values.append("control1")
        self.values.append(newValue)

    @Slot(int)
    def on_control2_valueChanged(self, newValue):
        self.values.append("control2")
        self.values.append(newValue)

    @asyncslot
    async def on_control3_valueChanged(self, newValue):
        self.values.append("control3")
        self.values.append(newValue)

    @asyncslot
    @Slot(str)
    async def on_control4_valueChanged(self, newValue):
        self.values.append("control4")
        self.values.append(newValue)


class TestSlotSelection(unittest.TestCase):
    def setUp(self) -> None:
        if QtCore.QCoreApplication.instance() is not None:
            self.app = QtCore.QCoreApplication.instance()
        else:
            self.app = QtCore.QCoreApplication([])

    def tearDown(self) -> None:
        self.app = None

    def test_decorated(self):
        values1 = []
        values2 = []
        values3 = []
        values4 = []

        def callback():
            w = Widget()

            w.values.clear()
            w.control1.valueChanged[int].emit(12)
            w.control1.valueChanged[str].emit('ha')
            values1[:] = w.values

            w.values.clear()
            w.control2.valueChanged[int].emit(12)
            w.control2.valueChanged[str].emit('ha')
            values2[:] = w.values

            w.values.clear()
            w.control3.valueChanged[int].emit(12)
            w.control3.valueChanged[str].emit('ha')
            values3[:] = w.values

            w.values.clear()
            w.control4.valueChanged[int].emit(12)
            w.control4.valueChanged[str].emit('ha')
            values4[:] = w.values

            self.app.quit()

        with using_asyncio_from_qt():
            QtCore.QTimer.singleShot(0, callback)
            if hasattr(self.app, "exec"):
                self.app.exec()
            else:
                self.app.exec_()

        if is_pyqt:
            self.assertEqual(values1, ["control1", 12, "control1", "ha"])
        else:
            self.assertEqual(values1, [])
        self.assertEqual(values2, ["control2", 12])
        if is_pyqt:
            self.assertEqual(values3, ["control3", 12, "control3", "ha"])
        else:
            self.assertEqual(values3, [])
        self.assertEqual(values4, ["control4", "ha"])


if __name__ == '__main__':
    # TODO: insert sync callback to check invocation order
    unittest.main()
