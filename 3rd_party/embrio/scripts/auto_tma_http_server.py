#!/usr/bin/env python3
"""HTTP server exposing the AutoTMA measurement sequence for remote control.

`auto_tma.auto_tma_main.main()` is otherwise only reachable from the local
Tkinter GUI (auto_tma_gui.py) or by running the module directly, so AutoTMA
cannot be driven from another machine. This node adds a small JSON/HTTP entry
point in front of it. Python 3.8 standard library only, no new dependencies.

This file lives under 3rd_party/embrio/ and adds nothing to auto_tma itself:
no upstream file is modified, and nothing here runs unless it is started
explicitly.

Usage (in a terminal with the catkin workspace sourced, while roscore and the
device nodes are up -- i.e. after the usual `roslaunch auto_tma
auto_tma.launch`):

    rosrun auto_tma auto_tma_http_server.py [--port 8300]

or through the launch file next to this one:

    roslaunch auto_tma auto_tma_http_server.launch [port:=8300]

API (JSON over HTTP):

    GET /status
        {"state": "idle|running|finished|failed", "running": bool,
         "params": {...}|null, "log": [str, ...], "last_error": str|null,
         "started_at": float|null, "finished_at": float|null}

    POST /start   body: {"tma_auto": bool, "tare_force": bool,
                         "measure_mode": 0|1|2, "number_of_sample": 1..10,
                         "motion_speed": 1..100}   (all optional, defaults
                         match auto_tma_main.main())
        202 {"status": "accepted", "params": {...}}
        400 on invalid parameters, 409 while a run is in progress.

There is deliberately NO /stop: main() has no interruption mechanism, so a run
always continues to its end once started.

Notes:
- Parameters are validated HERE before calling main(), because main() calls
  sys.exit(1) on bad values (which would silently kill the worker thread).
- tma_auto=False makes main() block on input() (Enter on THIS terminal at each
  step); use it only with an operator at the Manager PC.
- gui_log_cb is the only progress seam main() offers; its messages
  ('AutoTMA started', 'sample_id: ..., thickness: ...', 'AutoTMA finished')
  are collected into the status log.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import rospy

from auto_tma.auto_tma_main import main as auto_tma_main

DEFAULT_PORT = 8300
LOG_MAX = 200

DEFAULT_PARAMS = {
    "tma_auto": True,
    "tare_force": True,
    "measure_mode": 0,
    "number_of_sample": 2,
    "motion_speed": 100,
}


def validate_params(body):
    """Return validated params merged over defaults; raise ValueError."""
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    unknown = set(body) - set(DEFAULT_PARAMS)
    if unknown:
        raise ValueError("unknown parameter(s): %s" % ", ".join(sorted(unknown)))
    params = dict(DEFAULT_PARAMS)
    params.update(body)
    for key in ("tma_auto", "tare_force"):
        if not isinstance(params[key], bool):
            raise ValueError("%s must be a boolean" % key)
    for key in ("measure_mode", "number_of_sample", "motion_speed"):
        if not isinstance(params[key], int) or isinstance(params[key], bool):
            raise ValueError("%s must be an integer" % key)
    # Same ranges main() enforces via sys.exit(1); motion_speed max per
    # NextageNXAInterface.setup(speed=...).
    if params["measure_mode"] not in (0, 1, 2):
        raise ValueError("measure_mode must be 0 (AUTO), 1 (MANUAL) or 2 (SKIP)")
    if not 1 <= params["number_of_sample"] <= 10:
        raise ValueError("number_of_sample must be between 1 and 10")
    if not 1 <= params["motion_speed"] <= 100:
        raise ValueError("motion_speed must be between 1 and 100")
    return params


class RunState:
    """State of the single AutoTMA run slot, shared across request threads."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread = None
        self.state = "idle"
        self.params = None
        self.log = []
        self.last_error = None
        self.started_at = None
        self.finished_at = None

    def snapshot(self):
        with self._lock:
            return {
                "state": self.state,
                "running": self.state == "running",
                "params": dict(self.params) if self.params else None,
                "log": list(self.log[-LOG_MAX:]),
                "last_error": self.last_error,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
            }

    def append_log(self, message):
        with self._lock:
            self.log.append(str(message))
            del self.log[:-LOG_MAX]

    def start(self, params):
        """Launch main() in a worker thread; raise RuntimeError if busy."""
        with self._lock:
            if self.state == "running":
                raise RuntimeError("an AutoTMA run is already in progress")
            self.state = "running"
            self.params = params
            self.log = []
            self.last_error = None
            self.started_at = time.time()
            self.finished_at = None
            self._thread = threading.Thread(
                target=self._run, args=(params,), name="auto-tma-run", daemon=True
            )
            self._thread.start()

    def _run(self, params):
        try:
            auto_tma_main(
                tma_auto=params["tma_auto"],
                tare_force=params["tare_force"],
                measure_mode=params["measure_mode"],
                number_of_sample=params["number_of_sample"],
                motion_speed=params["motion_speed"],
                gui_log_cb=self.append_log,
            )
        # BaseException: main() may raise SystemExit; a vanished run must
        # surface as failed, never as a silently dead thread.
        except BaseException as e:
            rospy.logerr("AutoTMA run failed: %r" % (e,))
            with self._lock:
                self.state = "failed"
                self.last_error = repr(e)
                self.finished_at = time.time()
        else:
            with self._lock:
                self.state = "finished"
                self.finished_at = time.time()


RUN_STATE = RunState()


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._reply(200, RUN_STATE.snapshot())
        else:
            self._reply(404, {"error": "not found: %s" % self.path})

    def do_POST(self):
        if self.path != "/start":
            self._reply(404, {"error": "not found: %s" % self.path})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            params = validate_params(json.loads(raw.decode("utf-8")) if raw.strip() else {})
        except ValueError as e:
            self._reply(400, {"error": str(e)})
            return
        try:
            RUN_STATE.start(params)
        except RuntimeError as e:
            self._reply(409, {"error": str(e)})
            return
        self._reply(202, {"status": "accepted", "params": params})

    def log_message(self, fmt, *args):
        rospy.loginfo("auto_tma_http: " + fmt % args)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    # roslaunch appends the remapping arguments (__name:=, __log:=) to every
    # node's argv; myargv() drops them so argparse only sees our own flags.
    args = parser.parse_args(rospy.myargv()[1:])

    # main() uses rospy service proxies; the node must exist before any run.
    rospy.init_node("auto_tma_http", disable_signals=True)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    rospy.loginfo("auto_tma_http listening on 0.0.0.0:%d" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
