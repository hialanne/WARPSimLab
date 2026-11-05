"""Run pytest with inherited temp-directory ACLs in the Windows sandbox.

Python 3.13 gives mode 0700 directories a private Windows ACL that excludes
the sandbox token. Retain inherited ACLs instead, only for this test process.
Pass standard pytest arguments, including a fresh --basetemp under tests/.
"""

import os
from pathlib import Path
import sys

import pytest


original_mkdir = os.mkdir


def sandbox_mkdir(path, mode=0o777, *, dir_fd=None):
    if os.name == "nt" and mode == 0o700:
        mode = 0o777

    return original_mkdir(path, mode, dir_fd=dir_fd)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    os.mkdir = sandbox_mkdir
    try:
        result = pytest.main(sys.argv[1:])
    finally:
        os.mkdir = original_mkdir

    raise SystemExit(result)
