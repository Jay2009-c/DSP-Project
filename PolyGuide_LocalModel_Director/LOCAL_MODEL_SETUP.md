# PolyGuide local model setup

## 1. Put the model in the project

```text
PolyGuide_LocalModel_Directory/
└── models/
    └── your-model.gguf
```

PolyGuide automatically finds the first `.gguf` file in `models/`.

## 2. Install the GGUF runtime

```bash
pip install llama-cpp-python
```

## 3. Run PolyGuide

```bash
python main.py
```

## 4. Choose the response mode

### Hybrid

`AI DIRECT: OFF`

The existing deterministic engine remains in control of normal menu-style questions. Complex, explanatory, comparative, or unseen questions can be sent to the local model.

### AI Direct

`AI DIRECT: ON`

Typed questions go directly to the local model. The application does **not** classify the message into an intent first.

The model receives the complete local `data/college.json` contents so it can inspect relationships across admission, departments, fees, facilities, and contact records. Verification flags remain part of the supplied data, and the model is instructed to distinguish verified from unverified records.

This is the mode to use when you want the model to understand natural-language questions such as:

- `I finished 10th and I am interested in computer engineering. What options are relevant to me?`
- `Compare the admission route and the fee information I have in this database.`
- `What information does the college database actually provide about student facilities?`
- `Can you answer this question using the college information you have, even though it does not match a predefined topic?`

If the model is unavailable, **AI Direct does not fall back to intent guessing**. It reports that the local model is unavailable instead.
