from pathlib import Path
import sys


def configure_local_packages():
    local_packages = Path(__file__).resolve().parent.parent / ".packages"
    local_packages_path = str(local_packages)
    if local_packages.exists() and local_packages_path not in sys.path:
        sys.path.insert(0, local_packages_path)
