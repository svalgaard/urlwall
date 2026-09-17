"""
URL-Wall configuration management.
"""

import os
import plistlib
import socket
import subprocess
import sys

import urlwall

ME = "urlwall"
CONFIG_VERSION = "1.0"
CFG_ROOT = os.path.expanduser(f"~/.{ME}")
CONFIG_FN = os.path.join(CFG_ROOT, "setup.plist")
_config = None


class Config:
    """Manages the URL-Wall configuration stored as a plist."""

    def __init__(self, fn):
        self.fn = fn
        self.read()

    # -- read/write setup --

    def read(self):
        if not os.path.isfile(self.fn):
            self.setupDefault()
        try:
            with open(self.fn, "rb") as f:
                self.plist = plistlib.load(f)
        except (OSError, plistlib.InvalidFileException) as e:
            print(f"Config read error: {e}", file=sys.stderr)
            self.setupDefault()

    def setupDefault(self):
        self.plist = {
            "configVersion": CONFIG_VERSION,
            "defaultBrowser": "Safari.app",
            "hostsAllowed": ["google.com"],
            "hostWithSubdomainsAllowed": [],
        }
        self.write()

    def write(self):
        self.plist["hostsAllowed"].sort()
        dn = os.path.dirname(self.fn)
        if not os.path.isdir(dn):
            os.makedirs(dn, exist_ok=True)
        try:
            with open(self.fn, "wb") as f:
                plistlib.dump(self.plist, f)
        except OSError as e:
            print(f"Config write error: {e}", file=sys.stderr)

    # -- browser --

    def getBrowser(self):
        return self.plist["defaultBrowser"]

    def setBrowser(self, br):
        curBrowser = self.getBrowser()
        if br != curBrowser:
            self.plist["defaultBrowser"] = br
            self.write()
            return br

    def setAsDefaultBrowser(self):
        """Set URL-Wall as macOS default browser for http/https/ftp."""
        bundle_id = "com.github.svalgaard.url-wall"
        schemes = ("http", "https", "ftp")
        entries = " ".join(
            f'{{CFBundleIdentifier="{bundle_id}",LSHandlerRoleViewer="{s}",LSHandlerContentClassName=""}}'
            for s in schemes
        )
        cmd = f"defaults write com.apple.LaunchServices LSHandlers -array-add {entries}"
        try:
            subprocess.run(["bash", "-c", cmd], check=True)
            print("Run `killall Finder` to apply the change.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting default browser: {e}", file=sys.stderr)
            return False

    # -- allowed hosts --

    def addAllowedHost(self, host):
        host = urlwall.getCanonicalHost(host)
        if not host:
            raise ValueError("Invalid host")
        if host not in self.plist["hostsAllowed"]:
            self.plist["hostsAllowed"].append(host)
            self.write()
            return host

    def addAllowedHostSubdomains(self, host):
        host = urlwall.getCanonicalHost(host)
        if not host:
            raise ValueError("Invalid host")
        if host not in self.plist["hostWithSubdomainsAllowed"]:
            self.plist["hostWithSubdomainsAllowed"].append(host)
            self.write()
            return host

    def removeAllowedHost(self, host):
        host = urlwall.getCanonicalHost(host)
        if not host:
            raise ValueError("Invalid host")
        if host in self.plist["hostsAllowed"]:
            self.plist["hostsAllowed"].remove(host)
            self.write()
            return host

    def removeAllowedHostSubdomains(self, host):
        host = urlwall.getCanonicalHost(host)
        if not host:
            raise ValueError("Invalid host")
        if host in self.plist["hostWithSubdomainsAllowed"]:
            self.plist["hostWithSubdomainsAllowed"].remove(host)
            self.write()
            return host

    # -- allow check --

    def isAllowed(self, url):
        host = urlwall.getCanonicalHost(url)
        if host in self.plist["hostsAllowed"]:
            return True
        if host in self.plist["hostWithSubdomainsAllowed"]:
            return True
        for p in self.plist["hostWithSubdomainsAllowed"]:
            if host.endswith("." + p):
                return True
        return False

    # -- log file (hostname-specific) --

    @property
    def logFile(self):
        hostname = socket.gethostname().split(".")[0]
        return os.path.join(CFG_ROOT, f"url-wall-{hostname}.log")


def getConfig(configFilename=CONFIG_FN):
    """Return the singleton Config instance."""
    global _config
    if _config is None:
        _config = Config(configFilename)
    return _config
