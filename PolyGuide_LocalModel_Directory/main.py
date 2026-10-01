"""Run: python main.py | terminal mode: python main.py --cli"""
import sys
from engine import ChatEngine


def main():
    try:
        engine = ChatEngine()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Could not load data/college.json:", exc, file=sys.stderr)
        return 1

    cli = "--cli" in sys.argv[1:]
    if cli:
        print("PolyGuide:", engine.home().text)
        print("Type 'quit' to exit. Home and Back are supported.")
        while True:
            try:
                question = input("\nYou: ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if question.strip().lower() in ("quit", "exit"):
                break
            reply = engine.respond(question)
            print("\nPolyGuide:", reply.text)
            print("Options:", " | ".join(reply.choices))
        return 0

    try:
        import tkinter as tk
        from gui import ChatApp
    except ImportError:
        print("Tkinter is missing. Check your Python distributor's Tkinter installation instructions.\n"
              "You can still run: python main.py --cli", file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Cannot open a desktop window:", exc, file=sys.stderr)
        print("Use a local desktop, or run: python main.py --cli", file=sys.stderr)
        return 1
    ChatApp(root, engine)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
