import os
import threading

VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

_lock = threading.Lock()


def get_visits() -> int:
    """Read current visit count from file. Returns 0 if file doesn't exist."""
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def increment_visits() -> int:
    """Atomically increment visit counter and persist to file. Returns new count."""
    with _lock:
        count = get_visits() + 1
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        # Write atomically via temp file + rename
        tmp = VISITS_FILE + ".tmp"
        with open(tmp, "w") as f:
            f.write(str(count))
        os.replace(tmp, VISITS_FILE)
        return count
