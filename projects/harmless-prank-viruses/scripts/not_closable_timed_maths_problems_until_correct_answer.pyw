import customtkinter as ctk
import random
import sys


sys.setrecursionlimit(1000000000)
ctk.set_appearance_mode("System")

OPEN_WINDOWS = []
SETTINGS = {
    "color_themes": ["blue", "green", "dark-blue"],
    "max_number": {
        "+": [1000, 50],
        "-": [1000, 50],
        "*": [25, 10],
        "/": [100, 10],
    },
    "problem_timer": 10,
    "win_size": (300, 220),
}


class MathsProblemWindow:
    window_count = 0

    def __init__(self, focus_win: bool = False):
        MathsProblemWindow.window_count += 1
        ctk.set_default_color_theme(SETTINGS["color_themes"][random.randint(0, len(SETTINGS["color_themes"]) - 1)])
        self.win = ctk.CTk()
        if not focus_win:
            self.win.iconify()
            self.win.deiconify()
        x = random.randint(0, self.win.winfo_screenwidth() - 300)
        y = random.randint(0, self.win.winfo_screenheight() - 200)
        self.win.geometry(f"{SETTINGS['win_size'][0]}x{SETTINGS['win_size'][1]}+{x}+{y}")
        self.win.title(f"Maths Problem {MathsProblemWindow.window_count}")
        self.win.bind("<Unmap>", self.on_iconify)
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        self.timer_id = None
        self.setup_ui()
        self.start()

    def setup_ui(self):
        self.timer = SETTINGS["problem_timer"]
        self.question_label = ctk.CTkLabel(self.win, font=ctk.CTkFont(size=40, weight="bold"))
        self.question_label.pack(pady=10)
        self.timer_label = ctk.CTkLabel(self.win, font=ctk.CTkFont(size=16))
        self.timer_label.pack()
        self.entry = ctk.CTkEntry(self.win, font=ctk.CTkFont(size=14))
        self.entry.bind("<Return>", lambda event: self.check_answer())
        self.entry.pack(pady=5)
        self.check_button = ctk.CTkButton(
            self.win, text="Check Answer", command=self.check_answer, text_color="white", corner_radius=8
        )
        self.check_button.pack(pady=5)
        self.result_label = ctk.CTkLabel(self.win, text="", font=ctk.CTkFont(size=12))
        self.result_label.pack(pady=5)
        OPEN_WINDOWS.append(self.win)

    def problem(self) -> tuple:
        operation = random.choice(["+", "-", "*", "/"])
        num1 = random.randint(1, SETTINGS["max_number"][operation][0])
        num2 = random.randint(1, SETTINGS["max_number"][operation][1])
        if operation == "/":
            num1 = num2 * random.randint(1, SETTINGS["max_number"][operation][0] // num2)
        question = f"{num1} {operation} {num2}"
        return num1, num2, operation, question, int(eval(question))

    def reset(self, timer: int):
        if self.timer_id: self.win.after_cancel(self.timer_id)
        self.num1, self.num2, self.operation, self.question, self.answer = self.problem()
        self.question_label.configure(text=self.question)
        self.result_label.configure(text="")
        self.entry.delete(0, "end")
        self.timer = timer
        self.update_timer()

    def update_timer(self):
        if self.timer > 0:
            self.timer_label.configure(text=f"Time left: {self.timer}s")
            self.timer -= 1
            self.timer_id = self.win.after(1000, self.update_timer)
        else:
            self.result_label.configure(text="Time is up!", text_color="red")
            self.reset(SETTINGS["problem_timer"])
            MathsProblemWindow()

    def check_answer(self):
        user_answer = self.entry.get()
        if user_answer.isdigit() and int(user_answer) == self.answer:
            if self.timer_id: self.win.after_cancel(self.timer_id)
            for after_id in self.win.tk.call("after", "info"):
                self.win.after_cancel(after_id)
            OPEN_WINDOWS.remove(self.win)
            self.win.destroy()
        else:
            self.result_label.configure(text="Wrong answer! Try again.", text_color="red")
            self.reset(SETTINGS["problem_timer"])
            MathsProblemWindow()

    def on_close(self):
        self.result_label.configure(text="Close the window by solving the problem.", text_color="#40DFBD")

    def on_iconify(self, _):
        self.win.deiconify()
        self.result_label.configure(text="Minimizing the window is illegal!", text_color="#EE8050")

    def start(self):
        self.reset(SETTINGS["problem_timer"] + 1)
        self.win.mainloop()


if __name__ == "__main__":
    MathsProblemWindow(focus_win=True)
