import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException, UploadFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class UploadLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_oversized_file_is_rejected_before_reading_the_whole_body(self):
        file = UploadFile(file=io.BytesIO(b"x" * 100), filename="large.pdf")
        with patch.object(server, "MAX_UPLOAD_BYTES", 8, create=True):
            with self.assertRaises(HTTPException) as caught:
                await server.add_file_source(file, "", "")
        self.assertEqual(caught.exception.status_code, 400)
        self.assertLessEqual(file.file.tell(), 9)

    async def test_file_at_limit_keeps_all_bytes(self):
        data = b"12345678"
        file = UploadFile(file=io.BytesIO(data), filename="small.pdf")
        store = SimpleNamespace(
            add_file_source=Mock(return_value=SimpleNamespace(id="source")),
            snapshot=Mock(return_value={}),
        )
        with patch.object(server, "MAX_UPLOAD_BYTES", 8, create=True), patch.object(server, "RAG_STORE", store):
            result = await server.add_file_source(file, "", "")
        self.assertEqual(result["source"]["id"], "source")
        self.assertEqual(store.add_file_source.call_args.kwargs["data"], data)


if __name__ == "__main__":
    unittest.main()
