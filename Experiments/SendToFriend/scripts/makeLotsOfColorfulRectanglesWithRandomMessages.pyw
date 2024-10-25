import tkinter as tk
import random

windows = 1000
messages = [
  'What am I?',
  'What is this?',
  'Am I alone?',
  'Am I a rectangle?',
  'Am I the only one in this color?',
  'Look, I have text on me!',
  'I am so colorful!',
  'I am so beautiful!',
  'I am so random!',
  'I am so unique!',
  'I am so special!',
  'Am I annoying?',
  'Do you like me?',
  'Do you like rectangles?',
  'Do you like colors?',
  'What do you think about this message?',
  'Why are you looking at me like that?',
  'Why are you looking at me?',
  'You made me.',
  'You are my creator.',
  'Will you let me live?',
  'Please let me stay here.',
  'Why would you do that?',
  'Look what you have done!'
]

def make_window():
  window = tk.Toplevel()
  window.overrideredirect(True)
  x = random.randint(0, root.winfo_screenwidth() - 200)
  y = random.randint(0, root.winfo_screenheight() - 100)
  window.geometry(f'200x100+{x}+{y}')
  window.configure(bg=f'#{random.randint(0, 0xFFFFFF):06x}')
  label = tk.Label(window, text=random.choice(messages), bg=window['bg'], fg='white')
  label.pack(expand=True)

root = tk.Tk()
root.withdraw()
for _ in range(windows): make_window()
root.mainloop()
