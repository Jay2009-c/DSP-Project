import sys
import types
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from local_model import LocalModelLayer


class FakeLlama:
    def __init__(self, *args, **kwargs):
        self.chat_calls = 0
        self.completion_calls = 0

    def create_chat_completion(self, **kwargs):
        self.chat_calls += 1
        raise RuntimeError("no compatible chat template")

    def create_completion(self, **kwargs):
        self.completion_calls += 1
        return {"choices": [{"text": "The local model answered directly from the supplied data."}]}


class FakeLlamaModule(types.ModuleType):
    Llama = FakeLlama


class TestLocalModel(unittest.TestCase):
    def test_chat_failure_uses_plain_completion_and_stays_available(self):
        fake = FakeLlamaModule("llama_cpp")
        old = sys.modules.get("llama_cpp")
        sys.modules["llama_cpp"] = fake
        try:
            model = LocalModelLayer(enabled=True)
            with tempfile.NamedTemporaryFile(suffix=".gguf") as model_file:
                model.model_path = model_file.name
                model._gguf = FakeLlama()
                model._availability = True
                answer = model.answer(
                    "Which departments are available and what is the approved fee?",
                    '{"college": {"name": "B.L. Patil Polytechnic"}}',
                    mode="direct",
                )
                self.assertIn("local model answered", answer.lower())
                self.assertTrue(model._availability)
                self.assertEqual(model._last_error, "")
                self.assertEqual(model._gguf.chat_calls, 1)
                self.assertEqual(model._gguf.completion_calls, 1)
        finally:
            if old is None:
                sys.modules.pop("llama_cpp", None)
            else:
                sys.modules["llama_cpp"] = old



if __name__ == "__main__":
    unittest.main()
