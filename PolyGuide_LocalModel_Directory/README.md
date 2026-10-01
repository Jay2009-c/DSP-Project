# PolyGuide - Working Prototype v1

A free, offline college information chatbot for a Data Structures using Python project.
Built from premise v1.0/v1.1 and the supplied UI concepts. This delivery is a
functional rule-based MVP, not the entire proposed micro-LLM architecture.

## 1. Start here

Use a local desktop/laptop with Python 3.10 or newer. No pip dependencies,
API key, account, paid service, database server, or internet connection is needed
by the application. Tkinter must be available in your Python installation.

1. Extract the ZIP completely. Do not run files inside the compressed ZIP view.
2. Open the extracted PolyGuide folder in VS Code or a terminal.
3. Check Python and Tkinter:

    python --version
    python -m tkinter

The second command should open a small test window. Close it.
4. Start the chatbot:

    python main.py

On Windows, if Python is invoked with `py`, use `py main.py` instead.
On systems where the command is `python3`, use `python3 main.py` instead.

Windows shortcut: double-click RUN_WINDOWS.bat. The terminal stays open after
exit so that startup errors can be read.

GUI-less fallback:

    python main.py --cli

CLI mode has no typing delay or bubbles. Type `quit` to exit.

Tkinter documentation: https://docs.python.org/3/library/tkinter.html
If Tkinter is absent, follow your Python distributor's installation instructions.
Online/headless notebooks generally cannot open this desktop window.

## 2. Try these interactions

- Admission -> 10th pass -> Documents -> Steps -> Dates.
- Type: What are the yearly fees for direct second year?
- Then select Computer Engineering.
- Type: What are the feees? (tests fuzzy intent matching).
- Courses -> Civil Engineering.
- More -> Facilities, or type Contact.
- Back restores the preceding conversation screen; Home resets topic context.
- F11 toggles full screen; Escape exits full screen.

The bot uses a 3-second timer and animated typing dots in the GUI. Sending is
temporarily disabled while waiting to preserve turn order. You can still scroll,
resize the window, and draft the next question. No blocking sleep is used.
Buttons change to match the current question. Large menus wrap in rows of three.
The layout is inspired by the sketches, not a pixel-perfect phone-image copy.

## 3. IMPORTANT: add actual college information

The college has not been identified and no official admission/fee information
was supplied. Therefore, this archive deliberately contains NO invented fees,
eligibility thresholds, dates, contacts, or claims about available facilities.
Computer, Mechanical and Civil are EXAMPLE branch labels only. Replace them
with the departments your college actually offers.

The app already runs and demonstrates the full conversation flow. Until you
populate the records, it explains that facts have not been verified.

Open data/college.json in a text editor. Each fact has this structure:

    {
      "text": null,
      "source": null,
      "updated": null,
      "verified": false
    }

Replace null with quoted text from a checked official source. Use an official
notice title/page/URL or an office confirmation as the source; set updated to
the actual verification date in YYYY-MM-DD format. Set verified to true only
after checking the answer. All four fields are required to display a fact.
The app checks the flag and presence of fields; it cannot independently certify
that a human-entered source is genuine or that a fact is still current.

For example, the place for direct-second-year Computer fees is:

    fees -> direct_second_year -> computer

Put the entire applicable official fee explanation in text, including academic
year, entry route, branch, category/concession scope, and whether it is tuition,
total annual fees, or an installment. Do not enter one unexplained amount.

Admission records are indexed by completed qualification, not automatically
inferred eligibility. Under each of 10th, 12th, iti, fill eligibility, steps,
documents, dates. Include subject requirements and official route distinctions.
If rules do not match these three categories, extend the code and data together.

Departments are dictionaries keyed by an internal identifier. To add one,
copy a department record and edit its key, name, aliases, and overview. Add
matching fee records under both entry-route keys. Buttons are generated from
these records, so no GUI edits are required for another department.

Fill facilities and contact as fact records too. Replace college.name and set
college.demo to false only after replacing example branch names and checking
the dataset. Restart the app after saving JSON. JSON uses double quotes and
has no comments or trailing commas. Keep the file UTF-8.

Missing records fail safely: the bot asks the student to confirm with the office.
Setting demo to false does NOT turn unverified records into verified facts.
Each displayed fact includes source and recorded date, plus a current-rule warning.

## 4. Files and data structures

main.py              Entry point, desktop/CLI selection and startup errors.
engine.py            Keyword/fuzzy search, conversational state, local facts and model routing.
gui.py               Tkinter window, rounded bubbles, quick buttons and timers.
data/college.json    Editable local knowledge base.
local_model.py       Optional local Ollama LLM adapter for generalisation/reasoning.
LOCAL_MODEL_SETUP.md Local-model installation, configuration and grounding notes.
tests/test_engine.py Automated engine tests.
RUN_WINDOWS.bat      Windows launch helper.

Dictionary: college data, trigger sets and keyed department/fee records.
Set: unique trigger vocabulary and token checks.
List: reply choices, ranked intent candidates and navigation history.
Stack: navigation_stack uses append/pop for Back (last in, first out).
Tree: MenuNode category tree supplies Home, Admission, Fees and Courses options.
Deque: bounded in-memory conversation history; oldest exchanges drop first.
Searching: exact token/phrase matching, then difflib typo matching.
Sorting: intent candidates ranked by descending trigger score.
State machine: asks qualification or entry route/department, then reads facts.

No linked list or binary search is claimed. A deque used for bounded history
should be described as bounded history, not as an unimplemented request queue.
The GUI handles one question at a time. This is a finite-state FAQ chatbot,
not a general-purpose AI assistant and not a guarantee of understanding every
paraphrase. Fee intent takes priority in fee/admission compound questions.
Prefer one independent topic per message.

## 5. Test and verify

From the extracted project folder:

    python -m unittest discover -s tests -v

The included tests cover admission/fee follow-ups, keyword typos, back/home,
unverified-record blocking, bounded history, menus and malformed root data.
They are engine tests, not visual GUI tests. Manually test window resizing,
scrolling, full screen, typing delay and close-during-typing on your computer.

## 6. Local model and AI scope

Copy the extracted folder to a USB and run main.py on a compatible computer
with Python and Tkinter already installed. This is NOT a standalone executable
or a bundled portable Python runtime. All paths are relative to the source file,
so the app is not tied to a specific drive letter.

The project now includes an optional local LLM layer. `local_model.py` talks to an
Ollama service on the same computer using Python's standard-library HTTP client,
so the PolyGuide Python project still has no required pip dependency or cloud API
key. The deterministic engine remains authoritative for navigation and simple fact
lookup. The local model is used as a generalisation/reasoning fallback for complex,
multi-part, explanatory and previously-unmatched questions.

The model receives verified records extracted from `data/college.json`; unverified
record text is excluded. It is explicitly instructed not to invent college facts.
If the model is unavailable, missing, stopped, or fails during a request, the original
rule-based engine remains usable. See `LOCAL_MODEL_SETUP.md` for setup and configuration.

The GUI keeps the same rich visual/interaction layer: rounded chat bubbles, quick-choice
chips, navigation buttons, scrolling, full screen, typing animation and bounded history.
Model generation runs in a worker thread so the Tkinter interface remains responsive
while a local model is thinking.

Chat history is stored in memory only; it is not written to disk or sent to a cloud service
by PolyGuide. The local model receives only the current question, a short recent conversation
window, current navigation state and verified local college context.

## 7. Common fixes

- Command not found: use the Python launcher installed on your system.
- Tkinter missing: consult your Python distributor. Try CLI mode meanwhile.
- Cannot open display: run on your local desktop rather than a remote notebook.
- JSON startup error: remove trailing commas; retain required top-level objects.
- Missing factual answer: supply text, source, updated and verified=true.
- Wrong topic: use Home and ask one question at a time; matching is rule-based.
- Expecting a self-contained USB app: this ZIP needs Python/Tkinter on the target.

## Documentation used

https://docs.python.org/3/library/tkinter.html
https://tkdocs.com/tutorial/eventloop.html
https://docs.python.org/3/library/difflib.html
https://docs.python.org/3/library/collections.html

## AI Direct mode

The rich GUI now has an **AI DIRECT** toggle. When enabled, typed questions bypass intent guessing and are answered directly by the local model against the college database. Explicit GUI buttons still perform navigation.

See `LOCAL_MODEL_SETUP.md` and `models/README.md` for model placement and setup.


## AI Direct inference failures

AI Direct mode does not route a failed model request into the intent engine. A GGUF can be detected and loaded successfully while an individual generation still fails, for example because a model does not expose a compatible chat template or a prompt is too demanding. PolyGuide now:

- keeps the loaded model available after an inference error;
- retries a GGUF without a chat-template dependency using plain completion;
- shows the last inference error in the model status instead of claiming the model is unloaded;
- keeps AI Direct free of intent-guessing fallback;
- continues using the deterministic engine as fallback only in Hybrid mode.

The bundled database is the real B.L. Patil Polytechnic, Khopoli dataset in `data/college.json`. Replace that file with another schema-compatible college dataset to reuse the prototype.
