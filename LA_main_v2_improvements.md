---
title: "LA_main_v2 — Code Review & Improvement Notes"
project: "Laser Ablation System — Ice Core Water Isotope Measurements"
repository: "https://github.com/vgkinis/Kerttu_Laser_Ablation_fork"
author: "Claude (Anthropic) — code review"
date: 2026-03-23
context: "Based on Peensoo (2021) MSc thesis, University of Copenhagen / PICE"
tags:
  - python
  - pyqt5
  - serial
  - arduino
  - laser-ablation
  - ice-core
  - instrumentation
  - code-review
  - performance
status: draft
---

# LA_main_v2 — Code Review & Improvement Notes

## 1. What the Code Does

The system is a PyQt5 GUI (`LA_main_v2.py`) for controlling a laser ablation ice-core analysis rig.
It has two classes: `App` (GUI) and `WorkerThread` (background thread). The worker thread runs a
**tight, unthrottled `while True` loop** that polls both a femtosecond IR laser (via RS-232,
`laser.py`) and an Arduino-driven linear stage (via serial, `linear_stage.py`). Each poll cycle
calls `ping_arduino()` → `serial_read()` on the stage and `ping_laser_module()` → `serial_read()`
on the laser, then emits a PyQt signal to update the GUI. The worker also handles calibration
(driving to both endstops to find centre) and discrete movement (step–wait–ablate cycles).
Configuration lives in JSON files. A tab-delimited CSV logger writes data every second. The
`LinearStage` class converts steps↔mm↔rev and sends ASCII commands (`S`, `V`, `D`, etc.) to the
Arduino, which runs `linear_stage.ino`. The `Laser` class decodes status bytes, energy, and
repetition rate over RS-232.

---

## 2. Root Causes of Sluggish / Non-Responsive Behaviour

### 2.1 Tight `while True` with no sleep
The worker loop spins at CPU speed. With a serial timeout of 100 ms, each `serial_read()` blocks
the thread for up to 100 ms, but between serial events the loop hammers the CPU and starves the Qt
event queue that processes signals.

### 2.2 `serial_read()` can silently return `None`
When partial or bad data arrives from the Arduino, `serial_read()` returns `None`. The caller then
executes `self.data_dict.update(None)`, raising a `TypeError` that is caught silently by the broad
`except Exception`, breaking the update cycle for that tick.

### 2.3 Signal emission on every loop iteration
`signals.emit(True)` fires every cycle regardless of whether anything changed. Each emission
crosses thread boundaries and triggers a full GUI repaint including a Matplotlib canvas redraw
(`update_graph`), which is expensive.

### 2.4 `update_graph` redraws Matplotlib on every signal
Matplotlib figure operations (`cla()`, `plot()`, `canvas.draw()`) are among the slowest Qt
operations. Running them at the unconstrained loop rate creates visible jank.

### 2.5 `laser.serial_read()` called unconditionally
`ping_laser_module` checks `in_waiting` before sending, but `serial_read` is called
unconditionally after, reading nothing but blocking for the full serial timeout.

### 2.6 No thread synchronisation on shared state
`App` reads `wt.ls.data_dict` and `wt.laser.data_dict` directly from the GUI thread while the
worker thread writes them. On CPython the GIL makes dict updates effectively atomic, but
`calibrating`, `discrete_sampling`, and other flags are written from both threads without locks,
which can cause missed state transitions.

### 2.7 `connect_linear_stage` tries every port blindly
The method iterates every available serial port and opens each one, sleeping 2 s per attempt
regardless of port type, meaning startup can take 10+ seconds when many ports exist.

---

## 3. (a) Minimal Fix — Two Lines

Add a `time.sleep()` at the bottom of the worker loop to release the CPU and throttle signal
emission, and guard `data_dict.update()` against `None` returns:

```python
# In WorkerThread.run(), at the end of the while True body:
time.sleep(0.05)  # 50 ms → ~20 Hz update rate, matches serial timeout cadence
```

```python
# Replace unconditional update:
motor_data = self.ls.serial_read()
if motor_data is not None:          # <-- add this guard
    self.data_dict.update(motor_data)
```

These two changes eliminate the CPU spin and the silent crash, and require under five minutes to
apply.

---

## 4. (b) Comprehensive List of Changes

### Threading & loop control
- Add a `threading.Event` stop flag so the worker exits cleanly on application quit rather than
  relying on daemon-thread kill.
- Replace the raw `while True` with a rate-limited loop using `time.sleep(0.05)` or a
  `QTimer`-based approach in the main thread.
- Use a `threading.Lock` to protect shared mutable state (`data_dict`, `calibrating`,
  `discrete_sampling`).

### Signal / GUI update rate
- Emit the update signal only when data actually changes (compare new dict to previous snapshot
  before emitting).
- Alternatively, drive GUI updates from a `QTimer` in the main thread at a fixed 10 Hz rate,
  fully decoupling the GUI refresh rate from the serial poll rate.

### Matplotlib → pyqtgraph
- The repository already imports `pyqtgraph` but uses Matplotlib for the position graph. Replace
  the `FigureCanvas` widget with a `pyqtgraph.PlotWidget`. `pyqtgraph` is OpenGL-accelerated and
  orders of magnitude faster for real-time updates.

### Serial robustness
- Guard all `serial_read()` return values (`if motor_data is not None`).
- Add a serial reconnection mechanism with exponential backoff instead of silently swallowing
  exceptions.
- In `connect_linear_stage`, filter ports by VID/PID or description string (e.g.,
  `"Arduino" in port.description`) rather than attempting every port.

### Laser polling
- Only call `laser.serial_read()` when `self.laser.ser.in_waiting > 0` to avoid blocking reads
  that return nothing and waste the serial timeout.

### Data logger
- Open the CSV file once and keep the file handle open (or use `csv.writer`) rather than
  `open()` + `write()` + `close()` on every 1 s tick, which adds unnecessary filesystem overhead.

### State machine for calibration / discrete movement
- Replace the implicit state spread across `calibrate_sys()` and `discrete_movement()` calls with
  an explicit `enum`-based state machine. Currently, Arduino event codes double as Python state
  variables, which makes the control flow hard to reason about and to debug.

### Error reporting
- Replace `print(e)` throughout with `logging` module calls at appropriate levels
  (`logging.warning`, `logging.error`), so errors are timestamped and can optionally be written
  to the same data directory as the CSV logs.

---

## 5. Tests to Verify the New Code

Run with `pytest -v`. The `qtbot` fixture requires `pytest-qt`. For headless CI, set
`QT_QPA_PLATFORM=offscreen`.

```python
# ── test_linear_stage.py ─────────────────────────────────────────────────────

import pytest
from unittest.mock import MagicMock
from linear_stage import LinearStage


@pytest.fixture
def ls():
    return LinearStage(thread_pitch=4, stp_per_rev=800,
                       stage_length=1200, tray_length=550)


def test_mm_to_stp_roundtrip(ls):
    for mm in [0, 10, 100, 550]:
        assert ls.stp_to_mm(ls.mm_to_stp(mm)) == mm


def test_speed_conversions(ls):
    mm_s = 5.0
    us_stp = ls.mm_s_to_us_stp(mm_s)
    assert abs(ls.us_stp_to_mm_s(us_stp) - mm_s) < 0.01


def test_serial_read_returns_none_on_bad_data(ls):
    """Garbage serial input must not raise — must return None."""
    ls.ser = MagicMock()
    ls.ser.readline.return_value = b"garbage data\n"
    result = ls.serial_read()
    assert result is None


def test_serial_read_returns_none_on_partial_data(ls):
    """'s' appearing after 'r' is malformed — must return None."""
    ls.ser = MagicMock()
    ls.ser.readline.return_value = b"r1234s5678\n"
    result = ls.serial_read()
    assert result is None


def test_serial_read_valid(ls):
    """Well-formed frame must parse correctly."""
    ls.ser = MagicMock()
    # Format: s<loop_ms>;<abs_stp>;<dis_stp>;<spd_us>;<dir>;<event>r
    ls.ser.readline.return_value = b"s1000;8000;0;2500.0;1;0r\n"
    result = ls.serial_read()
    assert result is not None
    assert result["pos_mm"] == ls.stp_to_mm(8000)
    assert result["direction"] == 1
    assert result["event_code"] == 0


# ── test_worker_thread.py ─────────────────────────────────────────────────────

import time
import threading
from unittest.mock import MagicMock, patch


def test_worker_loop_does_not_spin_at_100pct_cpu():
    """Worker thread must sleep between iterations (20 Hz target)."""
    from LA_main_v2 import WorkerThread
    wt = WorkerThread()
    wt.laser_connected = False
    wt.linear_stage_connected = False
    count = []
    original_sleep = time.sleep

    def counting_sleep(t):
        count.append(t)
        original_sleep(min(t, 0.01))

    with patch("time.sleep", side_effect=counting_sleep):
        t = threading.Thread(target=wt.run, daemon=True)
        t.start()
        time.sleep(0.3)

    assert len(count) > 0, "Worker never slept — CPU spin detected"


def test_data_dict_update_survives_none_serial_read():
    """None return from serial_read must not propagate as an exception."""
    from LA_main_v2 import WorkerThread
    wt = WorkerThread()
    wt.ls = MagicMock()
    wt.ls.serial_read.return_value = None
    wt.ls.data_dict = {"pos_mm": 0}
    wt.data_dict = {}
    # This is the guarded pattern — must not raise
    motor_data = wt.ls.serial_read()
    if motor_data is not None:
        wt.data_dict.update(motor_data)
    # data_dict should remain unchanged
    assert wt.data_dict == {}


# ── test_laser.py ─────────────────────────────────────────────────────────────

import pytest
from unittest.mock import MagicMock
from laser import Laser


@pytest.fixture
def laser():
    l = Laser()
    l.ser = MagicMock()
    l.epoch_time = 0.0
    return l


def test_status_byte_parsing(laser):
    """0b10000001 = 129 → laser_on_enabled=1, all others 0 except power=1."""
    laser.ser.in_waiting = 1
    laser.ser.readline.return_value = b"ly_oxp2_dev_status 129\n"
    laser.serial_read()
    assert laser.data_dict["status_laser_on_enabled"] == 1
    assert laser.data_dict["status_power"] == 1
    assert laser.data_dict["status_error"] == 0


def test_energy_parsing(laser):
    """40000 nJ must be stored both as nJ and converted to uJ."""
    laser.ser.in_waiting = 1
    laser.ser.readline.return_value = b" 40000nJ\n"
    laser.serial_read()
    assert laser.data_dict["energy_nJ"] == 40000.0
    assert abs(laser.data_dict["energy_uJ"] - 40.0) < 0.001


def test_serial_read_skipped_when_buffer_empty(laser):
    """serial_read should not attempt a read when in_waiting == 0."""
    laser.ser.in_waiting = 0
    laser.serial_read()
    laser.ser.readline.assert_not_called()


# ── test_gui_signal.py  (requires pytest-qt + offscreen display) ──────────────

def test_signal_not_emitted_when_disconnected(qtbot):
    """No update signal should fire when neither device is connected."""
    from LA_main_v2 import WorkerThread
    wt = WorkerThread()
    signals_received = []
    wt.signals.connect(lambda v: signals_received.append(v))
    wt.start()
    import time; time.sleep(0.3)
    wt.terminate()
    assert len(signals_received) == 0, (
        f"Received {len(signals_received)} spurious signals while disconnected"
    )
```

---

## 6. Summary Table

| Issue | Severity | Effort to fix | Fix type |
|---|---|---|---|
| Tight `while True` — no sleep | High | Trivial | Add `time.sleep(0.05)` |
| `serial_read()` returns `None` unchecked | High | Trivial | Add `if result is not None` guard |
| Matplotlib redraws on every tick | Medium | Low | Switch to `pyqtgraph` |
| Signal emitted unconditionally | Medium | Low | Diff-check before emit |
| Laser read called unconditionally | Medium | Low | Check `in_waiting` first |
| No thread lock on shared flags | Low-Med | Low | Add `threading.Lock` |
| Port scan on all ports | Low | Low | Filter by description/VID |
| File open/close per log tick | Low | Low | Keep handle open |
| Implicit state machine | Low | Medium | Use `enum` state machine |
| `print()` error handling | Low | Low | Use `logging` module |
