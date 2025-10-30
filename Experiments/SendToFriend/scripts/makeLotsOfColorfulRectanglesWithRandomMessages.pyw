from random import randint, choice
import tkinter as tk


WINS = 1000
MSGS = [
    "Am I a rectangle?",
    "Am I alone?",
    "Am I annoying?",
    "Am I the only one in this color?",
    "Do you like colors?",
    "Do you like me?",
    "Do you like rectangles?",
    "I am everywhere!",
    "I am so beautiful!",
    "I am so colorful!",
    "I am so random!",
    "I am so special!",
    "I am so unique!",
    "I am unstoppable!",
    "Look at me!",
    "Look what you have done!",
    "Look, I have text on me!",
    "Please don't delete me.",
    "Please let me stay here.",
    "What am I?",
    "What are you doing?",
    "What do you think about this message?",
    "What do you want from me?",
    "What is this?",
    "Why are you looking at me like that?",
    "Why are you looking at me?",
    "Why did you create me?",
    "Why did you do this?",
    "Why do I exist?",
    "Why me?",
    "Why would you do that?",
    "Will you let me live?",
    "Will you let me stay?",
    "You are my creator.",
    "You made me.",
    "You should be proud of me.",
    "You will never be rid of me.",
    "You will never get rid of me.",
]


def make_window():
    win = tk.Toplevel()
    win.overrideredirect(True)
    x = randint(0, root.winfo_screenwidth() - 200)
    y = randint(0, root.winfo_screenheight() - 100)
    win.geometry(f"200x100+{x}+{y}")
    win.configure(bg=f"#{randint(0, 0xFFFFFF):06x}")
    label = tk.Label(win, text=choice(MSGS), bg=win["bg"], fg="white")
    label.pack(expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    for _ in range(WINS):
        make_window()
    root.mainloop()
