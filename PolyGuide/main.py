"""Run: python main.py | terminal mode: python main.py --cli"""
import argparse
import sys
from engine import ChatEngine

def main():
    parser = argparse.ArgumentParser(description="PolyGuide offline college chatbot")
    parser.add_argument("--cli", action="store_true", help="Use the terminal instead of a GUI")
    args = parser.parse_args()
    try:
        engine = ChatEngine()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("Could not load data/college.json:", exc, file=sys.stderr)
        return 1
    if args.cli:
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
