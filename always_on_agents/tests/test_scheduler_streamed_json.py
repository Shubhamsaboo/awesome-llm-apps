"""Scheduler options must survive requests without a Content-Length header."""

import ast
from json import JSONDecodeError
from pathlib import Path
from typing import Any
import unittest

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.testclient import TestClient


class StreamedSchedulerTests(unittest.TestCase):
    def clients(self):
        base = Path(__file__).resolve().parents[1]
        for folder in ("always_on_hn_briefing_agent", "release_radar_agent"):
            source = base / folder / "scheduler_api.py"
            node = next(n for n in ast.parse(source.read_text()).body
                        if isinstance(n, ast.AsyncFunctionDef) and n.name == "scheduler_trigger")
            app = FastAPI()
            # Keep the real route and request decoding; replace only scheduled work.
            namespace = {"app": app, "Request": Request, "Any": Any,
                         "JSONDecodeError": JSONDecodeError, "run_in_threadpool": run_in_threadpool,
                         "run_scheduled_scout": lambda payload: payload,
                         "run_scheduled_radar": lambda payload: payload}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
            route = next(route.path for route in app.routes if route.path.endswith("/trigger"))
            yield folder, TestClient(app), route

    def test_chunked_body_preserves_scheduling_options(self):
        for folder, client, route in self.clients():
            with self.subTest(app=folder), client:
                request = client.build_request(
                    "POST", route, content=iter([b'{"top_n": 3,', b'"dry_run": true}']),
                    headers={"Content-Type": "application/json"},
                )
                self.assertNotIn("content-length", request.headers)
                response = client.send(request)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"top_n": 3, "dry_run": True})

    def test_empty_and_malformed_bodies_keep_safe_defaults(self):
        for folder, client, route in self.clients():
            with self.subTest(app=folder), client:
                for data in (b"", b"not json"):
                    response = client.post(route, content=data)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), {})


if __name__ == "__main__":
    unittest.main()
