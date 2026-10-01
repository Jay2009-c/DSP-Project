"""College chatbot: local facts, intent search, state machine, tree and stack."""
import json
import re
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field
from difflib import get_close_matches

from local_model import LocalModelLayer

BASE = Path(__file__).resolve().parent

@dataclass
class Reply:
    text: str
    choices: list = field(default_factory=list)

@dataclass
class State:
    screen: str = "home"
    qualification: str = ""
    entry: str = ""
    department: str = ""

@dataclass
class MenuNode:
    label: str
    children: list = field(default_factory=list)

class ChatEngine:
    TRIGGERS = {
        "fees": {"fee", "fees", "cost", "tuition", "payment", "yearly fees"},
        "admission": {"admission", "admissions", "apply", "application", "eligibility", "eligible", "documents", "document", "deadline", "dates", "admission process"},
        "departments": {"department", "departments", "branch", "branches", "course", "courses"},
        "facilities": {"facility", "facilities", "library", "hostel", "canteen", "labs", "laboratory", "transport", "wifi"},
        "contact": {"contact", "phone", "email", "address", "location", "office", "website"},
    }
    def __init__(self, data=None, model=None, enable_model=True):
        if data is None:
            data = json.loads((BASE / "data" / "college.json").read_text(encoding="utf-8"))
        self.data = data
        self.validate(data)
        self.model = model if model is not None else LocalModelLayer(enabled=enable_model)
        self.state = State()
        self.navigation_stack = []
        self.history = deque(maxlen=200)
        self.menu_tree = MenuNode("Home", [
            MenuNode("Admission", [MenuNode("Steps"), MenuNode("Documents"), MenuNode("Eligibility"), MenuNode("Dates")]),
            MenuNode("Courses", [MenuNode(d["name"]) for d in data["departments"].values()]),
            MenuNode("Fees", [MenuNode("First year"), MenuNode("Direct second year")]),
            MenuNode("More", [MenuNode("Facilities"), MenuNode("Contact")]),
        ])
        self.vocabulary = sorted({w for values in self.TRIGGERS.values() for phrase in values for w in phrase.split()} | {"first", "second", "direct", "year"})

    @staticmethod
    def validate(data):
        if not isinstance(data, dict):
            raise ValueError("college.json must contain a JSON object.")
        for key in ("college", "admission", "departments", "fees", "facilities", "contact"):
            if key not in data or not isinstance(data[key], dict):
                raise ValueError("Missing or invalid object: " + key)
        if not data["departments"]:
            raise ValueError("Add at least one department record.")
        for key, dep in data["departments"].items():
            if not isinstance(dep, dict) or not isinstance(dep.get("name"), str):
                raise ValueError("Invalid department: " + key)
        for key in ("10th", "12th", "iti"):
            if not isinstance(data["admission"].get(key), dict):
                raise ValueError("Missing admission record: " + key)
        for key in ("first_year", "direct_second_year"):
            if not isinstance(data["fees"].get(key), dict):
                raise ValueError("Missing fees object: " + key)

    def tree_choices(self, label):
        node = self.menu_tree if label == "Home" else next((n for n in self.menu_tree.children if n.label == label), None)
        return [n.label for n in node.children] if node else []

    def move(self, screen, **fields):
        new = State(screen, self.state.qualification, self.state.entry, self.state.department)
        for key, value in fields.items():
            setattr(new, key, value)
        if new != self.state:
            self.navigation_stack.append(self.state)
            if len(self.navigation_stack) > 100:
                del self.navigation_stack[0]
            self.state = new

    def fact(self, record, label):
        if not isinstance(record, dict):
            record = {}
        text = record.get("text")
        source = record.get("source")
        date = record.get("updated")
        if record.get("verified") is not True or not text or not source or not date:
            return (label + " has not been verified in this local database yet.\n\n"
                    "Please confirm it with the college office. This prototype will not guess. "
                    "The project owner can add an official answer and its source in data/college.json.")
        return str(text) + "\n\nSource: " + str(source) + "\nRecorded/checked: " + str(date) + "\nConfirm current rules with the college before acting."

    def normalize(self, text):
        raw = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
        tokens = []
        for token in raw.split():
            if token in self.vocabulary or len(token) < 4 or any(c.isdigit() for c in token):
                tokens.append(token)
            else:
                matches = get_close_matches(token, self.vocabulary, n=1, cutoff=0.84)
                tokens.append(matches[0] if matches else token)
        return " ".join(tokens)

    @staticmethod
    def contains(text, phrase):
        return (" " + phrase + " ") in (" " + text + " ")

    def intent(self, text):
        scores = self.intent_candidates(text)
        if not scores:
            return None
        # A branch mentioned in a fee/admission question is a detail, not a topic switch.
        names = {name for _, name in scores}
        if "fees" in names:
            return "fees"
        if "admission" in names:
            return "admission"
        return scores[0][1]

    def intent_candidates(self, text):
        """Return every topic hit, ordered by strength, without forcing a single intent."""
        scores = []
        for name, phrases in self.TRIGGERS.items():
            score = sum(len(p.split()) for p in phrases if self.contains(text, p))
            if score:
                scores.append((score, name))
        scores.sort(key=lambda pair: (-pair[0], pair[1]))
        return scores

    def _is_complex_question(self, original, normalized, candidates):
        words = normalized.split()
        if len(words) >= 16:
            return True
        if len(candidates) >= 2:
            return True
        markers = (
            "why", "difference", "different", "compare", "comparison", "explain",
            "which should", "what if", "can i", "how does", "how do", "whether",
            "both", "all of", "step by step", "in simple words", "pros and cons",
        )
        return any(self.contains(normalized, marker) for marker in markers)

    def verified_context(self):
        """Build compact grounded context from verified records only."""
        lines = []
        college = self.data.get("college", {})
        if college.get("name") and not college.get("demo", True):
            lines.append("College: " + str(college["name"]))

        if not college.get("demo", True):
            for key, dep in self.data.get("departments", {}).items():
                if not isinstance(dep, dict):
                    continue
                name = dep.get("name")
                if name:
                    lines.append(f"Department {key}: {name}")

        def walk(node, path=()):
            if isinstance(node, dict):
                if {"text", "source", "updated", "verified"}.issubset(node.keys()):
                    if node.get("verified") is True and node.get("text") and node.get("source") and node.get("updated"):
                        path_text = " > ".join(path) or "record"
                        lines.append(
                            f"[{path_text}] {node['text']} | Source: {node['source']} | Checked: {node['updated']}"
                        )
                    return
                for key, value in node.items():
                    walk(value, path + (str(key),))
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, path + (str(index),))

        for root in ("admission", "departments", "fees", "facilities", "contact"):
            walk(self.data.get(root, {}), (root,))
        return "\n".join(lines)

    def full_data_context(self):
        """Build a complete, labelled view of the local college database.

        Unlike verified_context(), this includes unverified records too, but labels
        them explicitly so AI Direct mode can inspect everything actually provided
        without silently treating unverified records as confirmed facts.
        """
        payload = json.loads(json.dumps(self.data, ensure_ascii=False))
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _model_reply(self, original, normalized, candidates, direct=False):
        if not self.model or not getattr(self.model, "configured", False):
            return None
        context = self.full_data_context() if direct else self.verified_context()
        if not context:
            return None
        state = {
            "screen": self.state.screen,
            "qualification": self.state.qualification,
            "entry": self.state.entry,
            "department": self.state.department,
        }
        try:
            try:
                answer = self.model.answer(
                    original,
                    context,
                    history=list(self.history),
                    state=state,
                    mode="direct" if direct else "hybrid",
                )
            except TypeError:
                # Backwards compatibility for simple test/custom model adapters.
                answer = self.model.answer(
                    original,
                    context,
                    history=list(self.history),
                    state=state,
                )
        except Exception:
            answer = None
        if not answer:
            return None
        choices = self.view().choices
        return Reply(answer, choices)

    def refresh_model(self):
        """Rescan for a GGUF model and return its current status."""
        if self.model is None:
            return "LOCAL RULES | Model disabled"
        refresh = getattr(self.model, "refresh_model", None)
        if callable(refresh):
            try:
                return refresh()
            except Exception:
                pass
        return self.model_status()

    def model_status(self):
        if self.model is None:
            return "LOCAL RULES | Model disabled"
        status = getattr(self.model, "status_text", None)
        return status() if callable(status) else "LOCAL RULES | Model adapter unavailable"

    def qualification(self, text):
        if re.search(r"\b(10th|10|ssc|tenth)\b", text):
            return "10th"
        if re.search(r"\b(12th|12|hsc|twelfth)\b", text):
            return "12th"
        if self.contains(text, "iti"):
            return "iti"
        return ""

    def entry(self, text):
        if any(self.contains(text, p) for p in ("direct second year", "second year", "2nd year", "dsy", "lateral entry")):
            return "direct_second_year"
        if any(self.contains(text, p) for p in ("first year", "1st year", "fy")):
            return "first_year"
        return ""

    def department(self, text):
        words = set(text.split())
        for key, dep in self.data["departments"].items():
            aliases = [key, dep["name"].lower()] + [a.lower() for a in dep.get("aliases", [])]
            if any(self.contains(text, a) for a in aliases):
                return key
            candidates = [a for a in aliases if " " not in a and len(a) >= 5]
            if any(get_close_matches(w, candidates, n=1, cutoff=0.86) for w in words if len(w) >= 5):
                return key
        return ""

    def admissions_part(self, text):
        if any(self.contains(text, p) for p in ("documents", "document", "papers", "certificates")):
            return "documents"
        if any(self.contains(text, p) for p in ("dates", "date", "deadline", "last date")):
            return "dates"
        if any(self.contains(text, p) for p in ("steps", "step", "process", "apply", "application")):
            return "steps"
        return "eligibility"

    def home(self, greeting=False):
        text = ("Hi! I'm PolyGuide. Ask me about admission, courses, fees, facilities, or contacts. "
                "You can type or choose a button.")
        if self.data["college"].get("demo", True):
            text += "\n\nDEMO DATABASE: branch names are examples, and official college facts have not been entered."
        return Reply(text, self.tree_choices("Home"))

    def department_choices(self):
        return self.tree_choices("Courses")

    def view(self):
        s = self.state
        if s.screen == "home":
            return self.home()
        if s.screen == "more":
            return Reply("What would you like to check?", self.tree_choices("More"))
        if s.screen == "admission_qualification":
            return Reply("What is your completed qualification? This helps me find the right admission record; it does not confirm eligibility.", ["10th pass", "12th pass", "ITI pass"])
        if s.screen == "admission_details":
            return Reply("You're viewing the " + s.qualification.upper() + " qualification record. What do you want to check?", self.tree_choices("Admission"))
        if s.screen == "fees_entry":
            return Reply("Which entry route do you want the fee information for?", self.tree_choices("Fees"))
        if s.screen == "fees_department":
            return Reply("Which department's fees do you want?" + self.demo_note(), self.department_choices())
        if s.screen == "departments":
            return Reply("Select a department to view its locally stored information." + self.demo_note(), self.department_choices())
        if s.screen == "department_detail":
            dep = self.data["departments"][s.department]
            return Reply(self.fact(dep.get("overview"), dep["name"] + " details"), ["Courses", "Fees", "Admission"])
        if s.screen == "fees_result":
            dep = self.data["departments"][s.department]
            record = self.data["fees"][s.entry].get(s.department)
            route = "First year" if s.entry == "first_year" else "Direct second year"
            text = self.fact(record, route + " fees for " + dep["name"])
            return Reply(text, ["Fees", "Admission", "Contact"])
        if s.screen in ("facilities", "contact"):
            return Reply(self.fact(self.data[s.screen], s.screen.capitalize()), ["Admission", "Courses", "Fees"])
        return self.home()

    def demo_note(self):
        return "\n\nThese are example branches only, not a confirmed list for your college." if self.data["college"].get("demo", True) else ""

    def respond(self, text, direct_ai=False):
        text = text.strip()
        if not text:
            return Reply("Type a question or select an option.", self.view().choices)
        if len(text) > 1000:
            return Reply("Please keep the question under 1,000 characters.", self.view().choices)
        if direct_ai:
            reply = self._direct_ai_respond(text)
        else:
            reply = self._respond(text)
        self.history.append((text, reply.text))
        return reply

    def _direct_ai_respond(self, original):
        """Pure AI path: no intent detection, routing, or menu inference."""
        model_reply = self._model_reply(original, original.lower(), [], direct=True)
        if model_reply is not None:
            return model_reply
        status = self.model_status() if self.model is not None else "Local model unavailable"
        return Reply(
            "AI Direct mode is enabled, but the local model is not available right now.\n\n"
            + status
            + "\n\nNo intent-based fallback was used. Place a GGUF model in the models folder "
            "or start the configured local model server.",
            self.view().choices,
        )

    def _respond(self, original):
        t = self.normalize(original)
        if t in ("home", "menu", "start", "restart", "reset"):
            self.state = State()
            self.navigation_stack.clear()
            return self.home()
        if t in ("back", "go back", "previous"):
            if self.navigation_stack:
                self.state = self.navigation_stack.pop()
            return self.view()
        if t in ("hi", "hello", "hey", "help"):
            return self.home()
        if t in ("thanks", "thank you", "thankyou"):
            return Reply("You're welcome! You can choose another topic or type a question.", self.view().choices)
        if t == "more":
            self.move("more")
            return self.view()
        candidates = self.intent_candidates(t)
        intent = candidates[0][1] if candidates else None
        # Preserve deterministic handling for simple questions; use the local model
        # for genuinely multi-part, explanatory, comparative, or unseen wording.
        if candidates:
            names = {name for _, name in candidates}
            if "fees" in names:
                intent = "fees"
            elif "admission" in names:
                intent = "admission"
        q, entry, department = self.qualification(t), self.entry(t), self.department(t)
        screen = self.state.screen

        if self._is_complex_question(original, t, candidates) and self.model is not None:
            model_reply = self._model_reply(original, t, candidates)
            if model_reply is not None:
                return model_reply

        if intent == "fees":
            self.move("fees_entry", entry=entry, department=department or self.state.department)
            if entry:
                self.move("fees_department")
                if self.state.department:
                    self.move("fees_result")
            return self.view()
        if intent == "admission":
            is_details = screen == "admission_details"
            if q:
                self.move("admission_details", qualification=q)
            elif not is_details:
                self.move("admission_qualification", qualification="")
                return self.view()
            part = self.admissions_part(t)
            record = self.data["admission"][self.state.qualification].get(part)
            return Reply(self.fact(record, part.capitalize() + " for the " + self.state.qualification.upper() + " qualification record"), self.tree_choices("Admission"))
        if intent in ("facilities", "contact"):
            self.move(intent)
            return self.view()
        if intent == "departments":
            self.move("departments")
            if department:
                self.move("department_detail", department=department)
            return self.view()

        if screen == "admission_qualification":
            if q:
                self.move("admission_details", qualification=q)
                record = self.data["admission"][q].get("eligibility")
                return Reply(self.fact(record, "Eligibility for the " + q.upper() + " qualification record"), self.tree_choices("Admission"))
            return Reply("Please select 10th pass, 12th pass, or ITI pass. You can also switch topics using Home.", self.view().choices)
        if screen == "admission_details":
            if q:
                self.move("admission_details", qualification=q)
            if t in ("steps", "step", "process", "papers", "certificates", "date") or q:
                part = self.admissions_part(t)
                return Reply(self.fact(self.data["admission"][self.state.qualification].get(part), part.capitalize()), self.tree_choices("Admission"))
        if screen == "fees_entry":
            if entry:
                self.move("fees_department", entry=entry, department=department or self.state.department)
                if self.state.department:
                    self.move("fees_result")
                return self.view()
            if department:
                self.state.department = department
            return Reply("Please choose First year or Direct second year. A qualification alone does not establish your entry route.", self.tree_choices("Fees"))
        if screen == "fees_department":
            if department:
                self.move("fees_result", department=department)
                return self.view()
            return Reply("Please select a department from the buttons, or type its name.", self.department_choices())
        if department:
            self.move("department_detail", department=department)
            return self.view()
        if entry:
            return Reply("Do you want admission information or fee information for that route?", ["Admission", "Fees"])
        if q:
            self.move("admission_details", qualification=q)
            return Reply(self.fact(self.data["admission"][q].get("eligibility"), "Eligibility"), self.tree_choices("Admission"))
        model_reply = self._model_reply(original, t, candidates)
        if model_reply is not None:
            return model_reply
        return Reply("I couldn't match that question confidently. I can help with admission, courses, fees, facilities, and contacts. Try rephrasing it or choose a topic below.", self.tree_choices("Home"))
