"""Desktop GUI. Timer callbacks simulate typing without time.sleep()."""
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from collections import deque
from engine import ChatEngine

BG = "#062633"
HEADER = "#041a23"
BOT = "#153d4b"
USER = "#15586a"
TEXT = "#e4f1f4"
MUTED = "#8fadb8"
ACCENT = "#4cc9da"
DELAY_MS = 3000

class Bubble(tk.Canvas):
    def __init__(self, parent, text, sender, family):
        super().__init__(parent, bg=BG, highlightthickness=0, bd=0)
        self.text, self.sender, self.family = text, sender, family
        self.stamp = datetime.now().strftime("%I:%M %p")
        self.bind("<Configure>", self.redraw)

    def redraw(self, event=None):
        self.delete("all")
        w = max(self.winfo_width(), 200)
        max_width = min(int(w * 0.76), 640)
        color = USER if self.sender == "You" else BOT
        left = w - max_width - 12 if self.sender == "You" else 12
        content = self.create_text(left + 17, 39, text=self.text, anchor="nw", fill=TEXT,
                                   font=(self.family, 11), width=max_width - 34, justify="left")
        bbox = self.bbox(content)
        h = (bbox[3] if bbox else 65) + 37
        self.configure(height=h + 8)
        x1, y1, x2, y2, r = left, 4, left + max_width, h, 16
        points = [x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,
                  x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
        shape = self.create_polygon(points, smooth=True, fill=color, outline="")
        self.tag_lower(shape)
        self.create_text(left+17, 17, text=self.sender, anchor="nw", fill=ACCENT,
                         font=(self.family, 10, "bold"))
        self.create_text(left+17, h-22, text=self.stamp, anchor="nw", fill=MUTED,
                         font=(self.family, 8))

class ChatApp:
    def __init__(self, root, engine):
        self.root, self.engine = root, engine
        self.busy = False
        self.reply_job = self.animation_job = None
        self.typing = None
        self.phase = 0
        self.rows = deque()
        self.chip_buttons = []
        self.family = tkfont.nametofont("TkDefaultFont").actual("family")
        root.title("PolyGuide | College Information Chatbot")
        root.configure(bg=BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{min(1060, sw-60)}x{min(760, sh-90)}")
        root.minsize(560, 460)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.build()
        self.show_reply(self.engine.home())
        self.entry.focus_set()
        root.bind("<F11>", self.toggle_fullscreen)
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, font=(self.family, 10),
                         bg=ACCENT if primary else BOT, fg=HEADER if primary else TEXT,
                         activebackground="#246072", activeforeground=TEXT,
                         disabledforeground=MUTED, relief="flat", bd=0,
                         padx=14, pady=9, cursor="hand2", highlightthickness=1,
                         highlightbackground=ACCENT)

    def build(self):
        top = tk.Frame(self.root, bg=HEADER, padx=18, pady=14)
        top.pack(fill="x")
        self.back = self.button(top, "Back", lambda: self.send("Back"))
        self.back.pack(side="left", padx=(0, 16))
        titles = tk.Frame(top, bg=HEADER)
        titles.pack(side="left", fill="x", expand=True)
        tk.Label(titles, text="POLYGUIDE", bg=HEADER, fg=TEXT,
                 font=(self.family, 20, "bold"), anchor="w").pack(fill="x")
        name = self.engine.data["college"].get("name") or "Your Polytechnic College"
        tk.Label(titles, text=name, bg=HEADER, fg=MUTED, font=(self.family, 10),
                 anchor="w").pack(fill="x")
        self.home = self.button(top, "Home", lambda: self.send("Home"))
        self.home.pack(side="right")
        mode = "DEMO DATA | Example branches, unverified facts" if self.engine.data["college"].get("demo", True) else "LOCAL DATABASE | Check source and date in each answer"
        tk.Label(self.root, text=mode, bg="#103440", fg="#e4c583",
                 font=(self.family, 9), pady=6).pack(fill="x")

        bottom = tk.Frame(self.root, bg=HEADER)
        bottom.pack(side="bottom", fill="x")
        tk.Frame(bottom, height=2, bg=ACCENT).pack(fill="x")
        self.chips = tk.Frame(bottom, bg=HEADER, padx=16, pady=10)
        self.chips.pack(fill="x")
        input_row = tk.Frame(bottom, bg=HEADER, padx=16, pady=5)
        input_row.pack(fill="x")
        self.entry = tk.Entry(input_row, bg=BOT, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", font=(self.family, 12))
        self.entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send())
        self.send_button = self.button(input_row, "Send", self.send, primary=True)
        self.send_button.pack(side="right")
        self.status = tk.Label(bottom, text="Offline | No API key | F11: full screen",
                               bg=HEADER, fg=MUTED, font=(self.family, 8), pady=6)
        self.status.pack(fill="x")

        chat = tk.Frame(self.root, bg=BG)
        chat.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(chat, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.canvas = tk.Canvas(chat, bg=BG, highlightthickness=0,
                                yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG, pady=14)
        self.window = self.canvas.create_window(0, 0, window=self.inner, anchor="n")
        self.inner.bind("<Configure>", self.update_scroll)
        self.canvas.bind("<Configure>", self.resize_chat)
        self.root.bind_all("<MouseWheel>", self.wheel)
        self.root.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        self.root.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))

    def resize_chat(self, event):
        self.canvas.itemconfigure(self.window, width=min(event.width, 980))
        self.canvas.coords(self.window, event.width / 2, 0)
        self.update_scroll()

    def update_scroll(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def wheel(self, event):
        amount = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
        self.canvas.yview_scroll(amount, "units")

    def scroll_end(self):
        self.root.after_idle(lambda: self.canvas.yview_moveto(1.0))

    def add_message(self, text, sender):
        row = Bubble(self.inner, text, sender, self.family)
        row.pack(fill="x", pady=4)
        self.rows.append(row)
        while len(self.rows) > 200:
            self.rows.popleft().destroy()
        self.scroll_end()

    def show_reply(self, reply):
        self.add_message(reply.text, "PolyGuide")
        for widget in self.chips.winfo_children():
            widget.destroy()
        self.chip_buttons = []
        # Wrap long menus in rows of three, preserving every department option.
        for i, choice in enumerate(reply.choices):
            self.chips.columnconfigure(i % 3, weight=1)
            b = self.button(self.chips, choice, lambda c=choice: self.send(c))
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=4, pady=3)
            self.chip_buttons.append(b)

    def set_busy(self, value):
        self.busy = value
        state = "disabled" if value else "normal"
        for widget in [self.send_button, self.back, self.home] + self.chip_buttons:
            widget.configure(state=state)
        # Keep the entry editable so the next question can be drafted while waiting.
        self.status.configure(text="Preparing a local reply..." if value else "Offline | No API key | F11: full screen")

    def send(self, text=None):
        if self.busy:
            return
        text = self.entry.get().strip() if text is None else text.strip()
        if not text:
            return
        if len(text) > 1000:
            self.status.configure(text="Please shorten the question to 1,000 characters.")
            return
        self.entry.delete(0, "end")
        self.add_message(text, "You")
        self.set_busy(True)
        self.typing = tk.Label(self.inner, text="PolyGuide is typing .", bg=BG,
                               fg=MUTED, font=(self.family, 10), anchor="w", padx=28, pady=12)
        self.typing.pack(fill="x")
        self.phase = 0
        self.animate()
        self.reply_job = self.root.after(DELAY_MS, lambda: self.finish(text))
        self.scroll_end()

    def animate(self):
        if self.typing is not None:
            self.phase = (self.phase + 1) % 3
            self.typing.configure(text="PolyGuide is typing " + ". " * (self.phase + 1))
            self.animation_job = self.root.after(380, self.animate)

    def finish(self, text):
        self.reply_job = None
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        if self.typing:
            self.typing.destroy()
            self.typing = None
        reply = self.engine.respond(text)
        self.show_reply(reply)
        self.set_busy(False)
        self.entry.focus_set()

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def close(self):
        for job in (self.reply_job, self.animation_job):
            if job:
                self.root.after_cancel(job)
        self.root.destroy()
