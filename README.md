# qtinter — Interop between asyncio and Qt for Python

[![build](https://github.com/fancidev/qtinter/actions/workflows/build.yml/badge.svg)](https://github.com/fancidev/qtinter/actions/workflows/build.yml)
[![docs](https://readthedocs.org/projects/qtinter/badge/?version=latest)](https://qtinter.readthedocs.io/en/latest/?badge=latest)
[![tests](https://github.com/fancidev/qtinter/actions/workflows/tests.yml/badge.svg)](https://github.com/fancidev/qtinter/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/fancidev/qtinter/branch/master/graph/badge.svg?token=JZ5ON6CHKA)](https://codecov.io/gh/fancidev/qtinter)
[![PyPI](https://img.shields.io/pypi/v/qtinter)](https://pypi.org/project/qtinter/)

`qtinter` is a Python module that brings together asyncio and Qt
for Python, allowing you to use one from the other seamlessly.

## Quickstart

### Installation

```commandline
$ pip install qtinter
```

### Using asyncio from Qt

To use asyncio-based libraries in Qt for Python, enclose `app.exec()`
inside context manager `qtinter.using_asyncio_from_qt()`, and optionally
connect Qt signals to coroutine functions using `qtinter.asyncslot()`.

Minimal example (taken from `examples/sleep.py`):

```Python
import asyncio
import qtinter  # <-- import module
from PyQt6 import QtWidgets

async def sleep():
    button.setEnabled(False)
    await asyncio.sleep(1)
    button.setEnabled(True)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    button = QtWidgets.QPushButton()
    button.setText('Sleep for one second')
    button.clicked.connect(qtinter.asyncslot(sleep))  # <-- wrap coroutine function
    button.show()

    with qtinter.using_asyncio_from_qt():  # <-- enclose in context manager
        app.exec()
```

### Using Qt from asyncio

To use Qt components from asyncio-based code, enclose the asyncio
entry-point inside context manager `qtinter.using_qt_from_asyncio()`,
and optionally wait for Qt signals using `qtinter.asyncsignal()`.

Minimal example (taken from `examples/color.py`):

```Python
import asyncio
import qtinter  # <-- import module
from PyQt6 import QtWidgets

async def choose_color():
    dialog = QtWidgets.QColorDialog()
    dialog.show()
    result = await qtinter.asyncsignal(dialog.finished)  # <-- wait for signal
    if result == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.selectedColor().name()
    else:
        return None

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    with qtinter.using_qt_from_asyncio():  # <-- enclose in context manager
        color = asyncio.run(choose_color())
        if color is not None:
            print(color)
```

## Documentation

See full documentation at [qtinter.readthedocs.io](https://qtinter.readthedocs.io).


## Requirements

`qtinter` supports the following:

- Python version: 3.7 or higher
- Qt binding: PyQt5, PyQt6, PySide2, PySide6
- Operating system: Linux, MacOS, Windows


## Details


## Implementation Notes

By embedding a (logical) asyncio event loop inside a (physical) Qt event 
loop, what's not changed (from the perspective of the asyncio event loop) is 
that all calls (other than `call_soon_threadsafe`) are still made from the 
same thread.  This frees us from multi-threading complexities.

What has changed, however, is that in a standalone asyncio event loop, no 
code can run when the scheduler (specifically, `_run_once`) is blocked in 
`select()`, while in an embedded asyncio event loop, a `select()` call 
that would otherwise block yields, allowing any code to run while the loop 
is "logically" blocked in `select`.

For example, `BaseEventLoop.stop()` is implemented by setting the flag 
`_stopping` to `True`, which is then checked before the next iteration of
`_run_once` to stop the loop.  This works because `stop` can only ever be
called from a callback, and a callback can only ever be called after
`select` returns and before the next iteration of `_run_once`.  The behavior 
changes if `select` yields and `stop` is called -- the event loop wait not 
wake up until some IO is available.

We refer to code that runs (from the Qt event loop) after `select` yields 
and before `_run_once` is called again as _injected code_.  We must 
examine and handle the implications of such code.

We do this by fitting injected code execution into the standalone asyncio
event loop model.  Specifically, we treat injected code as if they were 
scheduled with `call_soon_threadsafe`, which wakes up the selector and
executes the code.  _With_ some loss of generality, we assume no IO event
nor timed callback is ready at the exact same time, so that the scheduler 
will be put back into blocking `select` immediately after the code finishes 
running (unless the code calls `stop`).  This simplification is acceptable
because the precise timing of multiple IO or timer events should not be 
relied upon.

In practice, we cannot actually wake up the asyncio scheduler every time 
injected code is executed, firstly because there's no way to detect their
execution and secondly because doing so would be highly inefficient.
Instead, we _assume_ that injected code which does not access the event loop
object or its selector is benign enough to be treated as _independent_
from the asyncio event loop ecosystem and may be safely ignored.

This leaves us to just consider injected code that accesses the event loop 
object or its selector and examine its impact on scheduling.  The scheduler
depends on three things:  the `_ready` queue for "soon" callbacks, the 
`_scheduled` queue for timer callbacks, and `_selector` for IO events.
If the injected code touches any of these things, it needs to be handled.

While the public interface of `AbstractEventLoop` has numerous methods, the 
methods that modify those three things boil down to `call_soon`, `call_at`, 
`call_later`, (arguably) `stop`, and anything that modifies the selector 
(proactor).  When any of these happens, we physically or logically wake up 
the selector to simulate a `call_soon_threadsafe` call.


## History

`asyncslot` is derived from
[qasync](https://github.com/CabbageDevelopment/qasync) but rewritten from 
scratch.  qasync is derived from 
[asyncqt](https://github.com/gmarull/asyncqt), which is derived from
[quamash](https://github.com/harvimt/quamash).


## License

BSD License.
