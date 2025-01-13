from xulbux import Console, Data
import subprocess
import platform


def check_vscode_installed() -> bool:
    try:
        command = "where" if platform.system() == "Windows" else "which"
        subprocess.run([command, "code"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def get_vscode_extensions() -> list[str]:
    try:
        result = subprocess.run(
            ["code", "--list-extensions"],
            capture_output=True,
            text=True,
            shell=True,
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        Console.fail(f"Failed to get extensions: {e.stderr}")


if __name__ == "__main__":
    if not check_vscode_installed():
        Console.fail("Visual Studio Code is not installed or not in PATH.")
    Data.print(get_vscode_extensions(), as_json=True)
