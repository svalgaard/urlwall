#!/usr/bin/env python3
"""
URL-Wall CLI entry point.

Usage:
    python -m urlwall [URL]                  # Open URL through the gate
    python -m urlwall --allow-host-add URL   # Add to allow list
    python -m urlwall --allow-host-remove URL # Remove from allow list
    python -m urlwall --also-subdomains      # Combine with --allow-host-add
    python -m urlwall --set-browser BROWSER  # Set browser used after URL-Wall
    python -m urlwall --use-as-default       # Set URL-Wall as macOS default browser
    python -m urlwall --install PATH         # Install .app bundle
"""

import argparse
import os
import sys

import urlwall
import urlwall.app
import urlwall.config as config


def main():
    parser = argparse.ArgumentParser(prog='url-wall')
    group = parser.add_mutually_exclusive_group()

    group.add_argument('url', metavar='URL', nargs='?',
                       help='URL to open. If no URL and no flags, prints config.')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--install', metavar='PATH',
                        help='Install URL-Wall as a .app bundle at PATH')

    # Config updates
    group.add_argument('--allow-host-add', '-a', metavar='URL',
                       help='Add host to allow list')
    group.add_argument('--allow-host-remove', metavar='URL',
                       help='Remove host from allow list')
    parser.add_argument('--also-subdomains', action='store_true',
                        help='Make --allow-host-add also apply for subdomains')
    group.add_argument('--set-browser', metavar='BROWSER',
                       help='Set browser to use after URL-Wall')
    group.add_argument('--use-as-default', action='store_true',
                       help='Set URL-Wall as the macOS default browser')

    args = parser.parse_args()

    if args.install is not None:
        app_path = os.path.expanduser(args.install)
        if os.path.isdir(app_path):
            print(f'Error: {app_path} already exists. Remove it first.', file=sys.stderr)
            sys.exit(1)
        urlwall.app.install(app_path)
        print(f'URL-Wall installed at {app_path}')
        return

    cfg = config.getConfig()

    if args.url is not None:
        urlwall.openURL(args.url)
    elif args.allow_host_add is not None:
        url = args.allow_host_add
        if args.also_subdomains:
            if host := cfg.addAllowedHostSubdomains(url):
                print(f'Added {host!r} incl. subdomains to allowed hosts')
        else:
            if host := cfg.addAllowedHost(url):
                print(f'Added {host!r} to allowed hosts')
    elif args.allow_host_remove is not None:
        url = args.allow_host_remove
        if host := cfg.removeAllowedHost(url):
            print(f'Removed {host!r} from allowed hosts')
        if host := cfg.removeAllowedHostSubdomains(url):
            print(f'Removed {host!r} incl. subdomains from allowed hosts')
    elif args.set_browser is not None:
        browser = args.set_browser
        if br := cfg.setBrowser(browser):
            print(f'Browser set to {br!r}')
        else:
            print(f'Browser already set to {browser!r}')
    elif args.use_as_default:
        if cfg.setAsDefaultBrowser():
            print('URL-Wall registered as default browser handler.')
        else:
            sys.exit(1)
    else:
        # Print current config summary
        print(f'Browser: {cfg.getBrowser()}')
        print(f'Allowed hosts: {", ".join(cfg.plist["hostsAllowed"])}')
        if cfg.plist['hostWithSubdomainsAllowed']:
            print(f'Allowed with subdomains: {", ".join(cfg.plist["hostWithSubdomainsAllowed"])}')


if __name__ == '__main__':
    main()
