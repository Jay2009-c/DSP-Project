# PolyGuide Local Models

Put **one GGUF language model file** in this folder:

```text
models/
└── your-model.gguf
```

PolyGuide automatically detects `.gguf` files when it starts. Detection is case-insensitive.
If more than one valid GGUF file is present, PolyGuide selects the largest file.

You can also add the model while PolyGuide is already running and press **↻ MODEL** in the top bar to rescan.

## Important: model file vs model runtime

The `.gguf` file is the model data. To execute it directly from Python, PolyGuide also needs the `llama-cpp-python` runtime:

```bash
pip install -r requirements-local-model.txt
```

Then restart PolyGuide, or press **↻ MODEL**.

The status bar distinguishes these states:

- `LOCAL MODEL READY` — GGUF was found and loaded successfully.
- `GGUF DETECTED` — the file was found, but the runtime is missing or the model could not load.
- `MODEL PATH INVALID` — an explicit model path points to a missing file.
- `OLLAMA` — no local GGUF was detected, so PolyGuide is checking the configured Ollama backend.

A GGUF file by itself is therefore not sufficient; a compatible local runtime must also be installed. The `llama-cpp-python` package exposes the `Llama` class and supports loading local GGUF files directly. See its current PyPI documentation for installation and platform-specific build options.
