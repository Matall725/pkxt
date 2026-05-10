from pathlib import Path
import sys


LOCAL_PACKAGES = Path(__file__).resolve().parent / ".packages"

if LOCAL_PACKAGES.exists():
    local_packages_path = str(LOCAL_PACKAGES)
    if local_packages_path not in sys.path:
        sys.path.insert(0, local_packages_path)
