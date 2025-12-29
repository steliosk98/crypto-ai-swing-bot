import sys
import os
import types

# Path to project root and src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ROOT = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

# Prefer local src/utils over any site-packages "utils" package.
utils_path = os.path.join(SRC_ROOT, "utils")
if os.path.isdir(utils_path):
    sys.modules.pop("utils", None)
    utils_pkg = types.ModuleType("utils")
    utils_pkg.__path__ = [utils_path]
    sys.modules["utils"] = utils_pkg
