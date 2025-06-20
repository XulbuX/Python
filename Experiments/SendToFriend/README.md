# Send To Friend
This repository contains **harmless** prank scripts (*also as [executables](./executables)*), that do all sorts of annoying things.
> [!CAUTION]
> These scripts lead to actions on your PC that you may not want.
> However, it is important to note that **none of these scripts will cause any damage to your PC**.


## addShutdownScriptToStartupFolderAndShutdownPC | [view script](./scripts/addShutdownScriptToStartupFolderAndShutdownPC.py)
This script/EXE will first create a second file `notSUS` in the user's startup directory.<br>
After that, it will start PC shutdown in `{time}` minutes display a message: `PC is shutting down in {time} minutes.`<br>
The `notSUS` file does the exact same thing (shutdown PC after `{time}` minutes and display message).<br>
Per default, the **`{time}` before shutdown is set to `5 minutes`**
### [Download](https://github.com/XulbuX/Python/raw/refs/heads/main/Experiments/SendToFriend/executables/addShutdownScriptToStartupFolderAndShutdownPC.exe)
> [!NOTE]
> This script/EXE works on all OSes.


## makeLotsOfColorfulRectanglesWithRandomMessages | [view script](./scripts/makeLotsOfColorfulRectanglesWithRandomMessages.pyw)
This script/EXE will simply create a bunch of colored rectangles on your screen and display a random message in each of them.<br>
There will be no way of getting rid of them, except for restarting your PC.
### [Download](https://github.com/XulbuX/Python/raw/refs/heads/main/Experiments/SendToFriend/executables/makeLotsOfColorfulRectanglesWithRandomMessages.exe)
> [!NOTE]
> This script/EXE works on all OSes.


## notClosableTimedMathsProblemsUntilCorrectAnswer | [view script](./scripts/notClosableTimedMathsProblemsUntilCorrectAnswer.pyw)
This script/EXE will create a small window with a math problem and a timer.<br>
If you enter the wrong answer or the timer runs out, the window will renew the problem and open a second math-problem-window.<br>
Trying to close or iconify the window will not work. The only way to close a math-problem-window is by entering the correct answer in time.
### [Download](https://github.com/XulbuX/Python/raw/refs/heads/main/Experiments/SendToFriend/executables/notClosableTimedMathsProblemsUntilCorrectAnswer.exe)
> [!NOTE]
> This script/EXE works on all OSes.


## playAnnoyingSoundsOnKeyboardAndMouse | [view script](./scripts/playAnnoyingSoundsOnKeyboardAndMouse.pyw)
This script/EXE will first copy itself to the user's startup directory, so that it will run on every system start.<br>
After that, it runs in the background and plays a sound every time the user presses a keyboard key/combination or clicks a mouse button.<br>
The volume can not be lowered lower than the set `MIN_VOLUME` (*default is 50%*) in the script. Muting will not work either.<br>
The only way to stop the script is by restarting the PC or by killing it in the task manager under the background processes (*the process is called the same as the scripts/EXEs name*).
### [Download](https://github.com/XulbuX/Python/raw/refs/heads/main/Experiments/SendToFriend/executables/playAnnoyingSoundsOnKeyboardAndMouse.exe)
> [!NOTE]
> This script/EXE works only on Windows.


## shutdownPCWithVirusWarning | [view script](./scripts/shutdownPCWithVirusWarning.py)
This script/EXE will shut down your PC five seconds after being run and display a shutdown message:<br>
`WARNING: Virus detected. Starting system clean up process...`<br>
The script/EXE are named a confusing and special looking name, to make it look like a very suspicious file.
### [Download](https://github.com/XulbuX/Python/raw/refs/heads/main/Experiments/SendToFriend/executables/shutdownPCWithVirusWarning.exe)
> [!NOTE]
> This script/EXE works on all OSes.
