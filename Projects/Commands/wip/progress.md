
## [x-clean](../x-clean.py) – System Cleaner CLI tool

**Features:**

-   **Registry cleanup** — scans uninstall keys + App Paths for entries pointing to missing paths
-   **Environment variables** — finds broken paths in PATH-style and single-value env vars (user + system)
-   **Shortcut cleanup** — resolves `.lnk` files and flags broken targets across Start Menu, Desktop, Startup
-   **Temp file cleanup** — scans User Temp, System Temp, and Prefetch

**Safety:**

-   Creates timestamped backups (`.reg` exports + JSON env var snapshots) before any changes
-   `--restore` flag to restore env vars from backup
-   Detailed summary + confirmation before executing

**Usage:**

-   `x-clean` — interactive mode (choose options → backup → scan → summary → confirm → execute)
-   `x-clean --help` — show help
-   `x-clean --restore "path/to/backup.json"` — restore env vars from backup

**Testing results on your system:**

-   11 broken uninstall entries (MinGW, Oracle Java, old VS Code, etc.)
-   4 broken App Paths entries
-   3 broken system env var paths
-   ~~3,568 temp files~~ (1.4 GB)
-   False positives for `InstallSource`/`DisplayIcon` and unexpanded `%VAR%` references were fixed
