# PolyGuide Local Models

Put exactly one GGUF model file in this directory, for example:

```text
models/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

PolyGuide automatically discovers the first `*.gguf` file here and loads it with `llama-cpp-python`.

Install the runtime once:

```bash
pip install llama-cpp-python
```

## AI DIRECT mode

The GUI contains an **AI DIRECT** toggle.

- **AI DIRECT: OFF** — normal hybrid mode. Deterministic intent/navigation handles simple questions and the local model helps with complex or unseen questions.
- **AI DIRECT: ON** — typed questions bypass intent guessing completely. The local model receives the college database directly and reasons over it. It preserves each record's `verified` status and must not invent missing information.

The Home, Back, and chip buttons remain explicit UI navigation commands even when AI DIRECT is enabled.
