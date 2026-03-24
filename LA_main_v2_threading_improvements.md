---
title: "LA_main_v2 — Threading & Loop Control Improvements"
project: "Laser Ablation System — Ice Core Water Isotope Measurements"
repository: "https://github.com/vgkinis/Kerttu_Laser_Ablation_fork"
file_target: "LA_main_v2.py"
author: "Claude (Anthropic) — code review"
date: 2026-03-23
related_notes:
  - "LA_main_v2_improvements.md"
tags:
  - python
  - pyqt5
  - threading
  - qthread
  - serial
  - instrumentation
  - code-review
  - concurrency
  - bug-fix
status: draft
priority: high
---

# LA_main_v2 — Threading & Loop Control Improvements

All changes are to `LA_main_v2.py` only. They are numbered in recommended
implementation order — each is self-contained and can be applied incrementally.

---

## Change 1 — Add `threading` and `logging` imports

**Where:** top of file, after the existing import block (line ~22).

**Why:** `threading` provides the `Event` and `Lock` primitives used by all
subsequent changes. `logging` replaces bare `print(e)` calls with timestamped,
levelled output that can also be written to a file alongside the data CSV.

```python
# ADD after existing imports
import threading
import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),            # keep console output
        logging.FileHandler("LA_errors.log")
    ]
)
```

---

## Change 2 — Add `_stop_event` and `_lock` to `WorkerThread.__init__`

**Where:** `WorkerThread.__init__` — currently only calls `QThread.__init__(self)`.

**Why:** Synchronisation primitives must be created in `__init__` so they exist
before `run()` is called and before `App` accesses them. Creating them inside
`run()` would be too late.

```python
# REPLACE
def __init__(self, parent=None):
    QThread.__init__(self)

# WITH
def __init__(self, parent=None):
    QThread.__init__(self)
    self._stop_event = threading.Event()   # set() this to exit the run loop cleanly
    self._lock = threading.Lock()          # protects shared flags against race conditions
```

---

## Change 3 — Move all variable initialisation from `run()` into `__init__`

**Where:** the block of assignments at the top of `WorkerThread.run()`, before
`time.sleep(2)`.

**Why:** Variables initialised inside `run()` do not exist until the thread
starts. `App.__init__` accesses `self.wt.calibrating`, `self.wt.discrete_sampling`,
etc. immediately after `wt.start()`, relying on a `time.sleep(1)` race to avoid
an `AttributeError`. Moving them to `__init__` eliminates that race entirely
(see also Change 8).

```python
# ADD all of the following into __init__, after the two lines from Change 2:
        self.discrete_sampling = False
        self.discrete_timer = None
        self.calibrating = False
        self.calibrate_start_count = None
        self.calibrated = False
        self.graph_half_range = None
        self.linear_stage_connected = False
        self.laser_connected = False
        self.ls = LinearStage(json_path="linear_stage.json")
        self.ls.read_json()
        self.laser = Laser()
        self.data_dict = {}
        self.data_dict.update(self.ls.data_dict)
        self.data_dict.update(self.laser.data_dict)
        self.logger_interval = 1
        self.logger_last_log_time = None

# run() then begins with just the warm-up delay and the loop:
def run(self):
    time.sleep(2)
    while not self._stop_event.is_set():
        ...  # see Change 4 for the full loop body
```

---

## Change 4 — Replace the `while True` loop body in `run()`

**Where:** the entire `while True` block inside `WorkerThread.run()`.

**What changes inside the loop:**
- `while True` → `while not self._stop_event.is_set()`
- `!= None` → `is not None` (correct Python sentinel idiom)
- Add `if motor_data is not None:` guard before `data_dict.update()`
- Replace `print(e)` with `logging.warning(...)`
- Add `time.sleep(0.05)` at the bottom, outside the `if` block

```python
def run(self):
    time.sleep(2)
    while not self._stop_event.is_set():

        if self.laser_connected or self.linear_stage_connected:
            self.signals.emit(True)

            if self.logger_last_log_time is not None:
                if self.logger_last_log_time + self.logger_interval <= time.time():
                    self.logger_last_log_time = time.time()
                    self.data_logger()

            if self.laser_connected:
                try:
                    self.laser.ping_laser_module()
                    self.laser.serial_read()
                    self.data_dict.update(self.laser.data_dict)
                except Exception as e:
                    logging.warning("Laser poll error: %s", e)

            if self.linear_stage_connected:
                try:
                    self.ls.ping_arduino()
                    motor_data = self.ls.serial_read()
                    if motor_data is not None:          # guard against bad serial frames
                        self.data_dict.update(motor_data)
                except Exception as e:
                    logging.warning("Linear stage poll error: %s", e)

                self.calibrate_sys()
                self.discrete_movement()

        time.sleep(0.05)    # ~20 Hz rate; releases CPU; placed outside the if-block
                            # so the loop sleeps even when both devices are disconnected
```

---

## Change 5 — Add a `stop()` method to `WorkerThread`

**Where:** new method in `WorkerThread`, directly after `run()`.

**Why:** Provides a clean, blocking shutdown path. `stop()` signals the loop to
exit via the event flag and then calls `self.wait()` to block until the `QThread`
finishes. This ensures serial ports are fully released before the process exits.

```python
def stop(self):
    self._stop_event.set()
    self.wait()    # block caller until QThread.run() returns
```

---

## Change 6 — Wrap shared flag reads and writes in `_lock`

**Where:** four locations across `App` and `WorkerThread`.

**Why:** `calibrating` and `discrete_sampling` are written from the GUI thread
(via button clicks) and read from the worker thread on every loop tick. Without
a lock, a write can be observed half-complete. On CPython the GIL makes this
unlikely in practice for simple bool assignments, but the lock makes the intent
explicit and future-proofs against non-CPython runtimes.

### 6a — `App.calibrate_sys()`

```python
# REPLACE
def calibrate_sys(self):
    if self.wt.linear_stage_connected == True and self.wt.discrete_sampling == False:
        self.wt.calibrating = True

# WITH
def calibrate_sys(self):
    if self.wt.linear_stage_connected and not self.wt.discrete_sampling:
        with self.wt._lock:
            self.wt.calibrating = True
```

### 6b — `App.reset_sys()`

```python
# REPLACE
def reset_sys(self):
    self.wt.calibrating = False
    self.wt.discrete_sampling = False
    self.wt.ls.reset_sys()

# WITH
def reset_sys(self):
    with self.wt._lock:
        self.wt.calibrating = False
        self.wt.discrete_sampling = False
    self.wt.ls.reset_sys()
```

### 6c — `WorkerThread.discrete_startup()`

```python
# REPLACE (first line of method body)
self.discrete_sampling = True

# WITH
with self._lock:
    self.discrete_sampling = True
```

### 6d — `WorkerThread.calibrate_sys()` and `WorkerThread.discrete_movement()`

Take a local snapshot of the flag under the lock before acting on it, so the
lock is held for the minimum time:

```python
# At the top of WorkerThread.calibrate_sys():
def calibrate_sys(self):
    with self._lock:
        calibrating = self.calibrating
    if calibrating:
        ...  # rest of method unchanged

# At the top of WorkerThread.discrete_movement():
def discrete_movement(self):
    with self._lock:
        sampling = self.discrete_sampling
    if sampling:
        ...  # rest of method unchanged
```

---

## Change 7 — Update `App.quit_app()` to call `wt.stop()`

**Where:** `App.quit_app()`.

**Why:** The current implementation calls `QApplication.instance().quit()` while
the worker thread is still running. This means the serial commands to the laser
and Arduino may not complete before the process exits. Calling `wt.stop()` first
blocks until the loop has exited cleanly.

```python
# REPLACE
def quit_app(self):
    if self.wt.linear_stage_connected:
        self.reset_sys()
    if self.wt.laser_connected:
        self.wt.laser.go_to_listen()
    QApplication.instance().quit()

# WITH
def quit_app(self):
    if self.wt.linear_stage_connected:
        self.reset_sys()
    if self.wt.laser_connected:
        self.wt.laser.go_to_listen()
    self.wt.stop()                      # signal loop exit and wait for thread to finish
    QApplication.instance().quit()
```

---

## Change 8 — Remove the `time.sleep(1)` race in `App.initUI()`

**Where:** `App.initUI()`, the line `time.sleep(1)` that appears after
`self.wt.start()`.

**Why:** This sleep exists solely to paper over the `AttributeError` that would
occur if the GUI accessed worker attributes before `run()` had initialised them.
Change 3 moves all initialisations to `__init__`, making this sleep unnecessary.
Removing it makes startup ~1 second faster and eliminates a fragile timing
dependency.

```python
# REMOVE this line entirely:
        time.sleep(1)
```

---

## Summary

| # | Location | Change | Reason |
|---|---|---|---|
| 1 | Top of file | Add `threading`, `logging` imports | Required by all other changes |
| 2 | `WorkerThread.__init__` | Add `_stop_event`, `_lock` | Synchronisation primitives |
| 3 | `WorkerThread.__init__` / `run` | Move variable init out of `run` | Eliminate startup race |
| 4 | `WorkerThread.run` | `while not stop_event`, `None` guard, `sleep(0.05)`, `logging` | Core loop fix |
| 5 | `WorkerThread` | Add `stop()` method | Clean shutdown |
| 6a | `App.calibrate_sys` | Wrap flag write in `_lock` | Thread safety |
| 6b | `App.reset_sys` | Wrap flag writes in `_lock` | Thread safety |
| 6c | `WorkerThread.discrete_startup` | Wrap flag write in `_lock` | Thread safety |
| 6d | `WorkerThread.calibrate_sys`, `discrete_movement` | Snapshot flags under `_lock` | Thread safety |
| 7 | `App.quit_app` | Call `wt.stop()` before quit | Clean serial shutdown |
| 8 | `App.initUI` | Remove `time.sleep(1)` | Race no longer exists |
