# CYCLONEX Backend Package
import os
import sys

_current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
_backend_dir = os.path.abspath(os.path.join(_current_dir, ".."))  # backend
_repo_root = os.path.abspath(os.path.join(_backend_dir, ".."))  # repository root

for _path in [_backend_dir, _repo_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

