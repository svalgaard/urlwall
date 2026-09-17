"""
Build a URL-Wall .app bundle from the AppleScript handler.

Usage:
    ./url-wall install ~/Applications/URL-Wall.app
    ./url-wall install -f ~/Applications/URL-Wall.app   # force overwrite
"""

import fnmatch
import os
import plistlib
import shutil
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_DIR = os.path.join(os.path.dirname(__file__), "app")


def _ignore_bundle(src, names):
    """Ignore files/dirs that don't belong in the .app bundle."""
    ignored = []
    for pattern in (
        "__pycache__",
        "*.pyc",
        ".git",
        ".gitignore",
        "tests",
        "*.egg-info",
        "dist",
        "build",
        ".venv",
        "venv",
        "*.egg",
        ".github",
        ".gitkeep",
    ):
        ignored.extend(fnmatch.filter(names, pattern))
    return set(ignored)


def patchInfo(appPath):
    """Patch the .app's Info.plist with URL scheme handlers."""
    infofn = os.path.join(appPath, "Contents/Info.plist")
    patchfn = os.path.join(APP_DIR, "Info-patch.plist")

    if not os.path.isfile(infofn):
        raise FileNotFoundError(f"Info.plist not found inside {appPath}")
    if not os.path.isfile(patchfn):
        raise FileNotFoundError(f"Info-patch.plist not found at {patchfn}")

    with open(patchfn, "rb") as f:
        patch = plistlib.load(f)
    with open(infofn, "rb") as f:
        info = plistlib.load(f)
    info.update(patch)
    with open(infofn, "wb") as f:
        plistlib.dump(info, f)


def install(appPath):
    """Build and install a URL-Wall .app bundle."""
    assert appPath.endswith(".app")

    scpt = os.path.join(APP_DIR, "url-wall.scpt")
    if not os.path.isfile(scpt):
        raise FileNotFoundError(f"AppleScript handler not found at {scpt}")

    # Compile AppleScript into .app
    subprocess.call(["/usr/bin/osacompile", "-o", appPath, scpt])

    # Patch with URL scheme handlers
    patchInfo(appPath)

    # Copy project assets into the bundle (exclude build artifacts, vcs, tests)
    assetsPath = os.path.join(appPath, "Contents/Resources/Assets")
    if os.path.isdir(assetsPath):
        shutil.rmtree(assetsPath)
    shutil.copytree(ROOT, assetsPath, ignore=_ignore_bundle)
