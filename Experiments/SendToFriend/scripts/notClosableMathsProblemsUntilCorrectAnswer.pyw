import customtkinter as ctk
import random

OPEN_WINDOWS = []
SETTINGS = {
    'colors': [
        '#FF0000',
        '#FF8000',
        '#FFFF00',
        '#BBFF00',
        '#00FF00',
        '#00FF9F',
        '#00FFFF',
        '#0080FF',
        '#0000FF',
        '#AA00FF',
        '#FF00FF',
        '#FF0080'
    ],
    'color_theme': 'blue',
    'change_color_timer': 25,
    'max_number1': 1000,
    'max_number2': 20,
    'problem_timer': 10
}

ctk.set_appearance_mode('System')
ctk.set_default_color_theme(SETTINGS['color_theme'])



class MathsProblemWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.timer = SETTINGS['problem_timer']
        self.win = ctk.CTk()
        self.win.geometry('300x200')
        self.win.title('Maths Problem')
        self.win.bind('<Unmap>', self.on_iconify)
        self.win.protocol('WM_DELETE_WINDOW', self.custom_close)
        self.num1, self.num2, self.operation, self.question, self.answer = self.problem(SETTINGS['max_number1'], SETTINGS['max_number2'])
        self.question_label = ctk.CTkLabel(self.win, text=f'Solve: {self.question}', font=ctk.CTkFont(size=16, weight='bold'))
        self.question_label.pack(pady=10)
        self.timer = SETTINGS['problem_timer']
        self.timer_label = ctk.CTkLabel(self.win, text=f'Time left: {self.timer}s', font=ctk.CTkFont(size=12))
        self.timer_label.pack(pady=5)
        self.entry = ctk.CTkEntry(self.win, font=ctk.CTkFont(size=14))
        self.entry.pack(pady=5)
        self.check_button = ctk.CTkButton(self.win, text='Check Answer', command=self.check_answer, fg_color='#000', text_color='white', corner_radius=8)
        self.check_button.pack(pady=5)
        self.result_label = ctk.CTkLabel(self.win, text='', font=ctk.CTkFont(size=12))
        self.result_label.pack(pady=5)
        OPEN_WINDOWS.append(self.win)

    def problem(max_num1:int, max_num2:int) -> tuple:
        num1 = random.randint(1, max_num1)
        num2 = random.randint(1, max_num2)
        operation = random.choice(['+', '-', '*'])
        question = f'{num1} {operation} {num2}'
        if operation == '+':   answer = num1 + num2
        elif operation == '-': answer = num1 - num2
        elif operation == '*': answer = num1 * num2
        return num1, num2, operation, question, answer

    def reset_problem(self):
        self.num1, self.num2, self.operation, self.question, self.answer = generate_problem()
        question_label.configure(text=f'Solve: {self.question}')
        result_label.configure(text='')
        entry.delete(0, 'end')
        nonlocal timer
        timer = SETTINGS['problem_timer']
        update_timer(self)

    def update_timer(self):
        nonlocal timer
        if timer > 0:
            timer_label.configure(text=f'Time left: {timer}s')
            timer -= 1
            window.after(1000, update_timer)
        else:
            result_label.configure(text='Time is up!', text_color='red')
            reset_problem()
            self.create_math_window()

    def check_answer():
        user_answer = entry.get()
        if user_answer.isdigit() and int(user_answer) == answer:
            window.destroy()
            if window in OPEN_WINDOWS:
                OPEN_WINDOWS.remove(window)
        else:
            result_label.configure(text='Wrong answer! Try again.', text_color='red')
            reset_problem()
            create_math_window()

    def custom_close():
        result_label.configure(text='Close the window by solving the problem.', text_color='blue')
        ctk.CTk().after(100, create_math_window)
        ctk.CTk().after(100, create_math_window)
        create_math_window()

    def on_iconify(event):
        result_label.configure(text='Minimizing the window is illegal!', text_color='orange')
        window.deiconify()
        ctk.CTk().after(100, create_math_window)
        ctk.CTk().after(100, create_math_window)
        create_math_window()

    color_index = [0]
    def change_color():
        window.configure(fg_color=SETTINGS['colors'][color_index[0]])
        color_index[0] = (color_index[0] + 1) % len(SETTINGS['colors'])
        window.after(SETTINGS['change_color_timer'], change_color)

    change_color()

    window.protocol('WM_DELETE_WINDOW', custom_close)
    window.bind('<Unmap>', on_iconify) 

    question_label = ctk.CTkLabel(window, text=f'Solve: {question}', font=ctk.CTkFont(size=16, weight='bold'))
    question_label.pack(pady=10)

    timer = SETTINGS['problem_timer']
    timer_label = ctk.CTkLabel(window, text=f'Time left: {timer}s', font=ctk.CTkFont(size=12))
    timer_label.pack(pady=5)

    entry = ctk.CTkEntry(window, font=ctk.CTkFont(size=14))
    entry.pack(pady=5)

    check_button = ctk.CTkButton(window, text='Check Answer', command=check_answer, fg_color='#000', text_color='white', corner_radius=8)
    check_button.pack(pady=5)

    result_label = ctk.CTkLabel(window, text='', font=ctk.CTkFont(size=12))
    result_label.pack(pady=5)

    update_timer()

    window.mainloop()



if __name__ == '__main__':
    MathsProblemWindow(ctk.CTk())
