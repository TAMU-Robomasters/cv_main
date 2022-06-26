
from pathlib import Path

def attempt_download(path):
    path = Path(str(path).strip().replace("'", ''))
    return str(path)