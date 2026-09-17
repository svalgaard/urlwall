# URL-Wall — Interceptive Browser for macOS

Add a confirmation step when you click an http, https, or ftp
URL *outside your browser* to ensure you reach the domain you expect.

Known domains go directly. Unknown domains show a warning page where you
can acknowledge and proceed.

## Installation

```bash
# Build the .app bundle
python -m urlwall --install ~/Applications/URL-Wall.app

# Set as macOS default browser
python -m urlwall --use-as-default
# Then run: killall Finder
```

## CLI Usage

```bash
# Open a URL through the gate
python -m urlwall https://example.com

# Add a domain to the allow list
python -m urlwall --allow-host-add example.com

# Add with subdomain support
python -m urlwall --allow-host-add example.com --also-subdomains

# Remove from allow list
python -m urlwall --allow-host-remove example.com

# Set the browser used after URL-Wall
python -m urlwall --set-browser "Google Chrome.app"

# Set URL-Wall as macOS default browser
python -m urlwall --use-as-default

# View current config
python -m urlwall
```

## How It Works

1. The `install` command compiles an AppleScript handler into a `.app` bundle
2. The `.app` is patched with URL scheme handlers (http, https, ftp)
3. When macOS routes a URL to URL-Wall, the AppleScript calls `python -m urlwall <url>`
4. The Python handler checks if the domain is allowed — if so, opens it directly
5. If not, shows a warning page with the full redirect chain and a "Proceed" button

## Configuration

Config is stored in `~/.urlwall/setup.plist`:

- `defaultBrowser` — app name (e.g., `Safari.app`)
- `hostsAllowed` — domains that open directly
- `hostWithSubdomainsAllowed` — domains + all subdomains
