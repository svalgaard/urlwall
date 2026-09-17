"""
URL-Wall CLI wrapper.

This script is placed in the .app bundle and called by the AppleScript handler.
It ensures the urlwall package is importable from the bundle context.

When called with no arguments, reads the URL from stdin (piped by AppleScript).
When called with arguments, passes them through to __main__.py.
"""

import os
import sys

# The .app bundle copies Assets/ at the same level as urlwall/
# So we need to add the Assets parent to sys.path
bundle_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if bundle_root not in sys.path:
    sys.path.insert(0, bundle_root)

from urlwall.__main__ import main

if __name__ == "__main__":
    # If called with no args, read URL from stdin (piped by AppleScript)
    if len(sys.argv) == 1 and not sys.stdin.isatty():
        url = sys.stdin.read().strip()
        if url:
            sys.argv = ["urlwall", url]
    main()
