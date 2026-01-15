# OpenLyst Multi-Platform Builds

This project provides builds for OpenLyst projects across multiple platforms.

https://openlyst.ink

## Unified Build Script

All repositories are generated using a single unified build script (`build.py`) that supports AltStore (iOS), F-Droid (Android), and Homebrew (macOS/Linux).

### Usage

```bash
# Build all repositories
python build.py --target all

# Build specific targets
python build.py --target altstore          # AltStore only
python build.py --target fdroid            # F-Droid only
python build.py --target homebrew          # Homebrew only
python build.py --target altstore,fdroid   # Multiple targets

# Homebrew platform options
python build.py --target homebrew --platform macOS   # macOS only
python build.py --target homebrew --platform Linux   # Linux only
python build.py --target homebrew --platform both    # Both platforms

# Additional options
python build.py --target all --calculate-sha256      # Calculate SHA256 hashes
python build.py --target all --verbose               # Verbose logging
```

### GitHub Actions

Run the "Build All Repositories" workflow to update all repositories at once, or use the individual workflows for specific targets.

---

## AltStore (iOS)

- Add this Source URL in AltStore: `https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/repo/apps.json`
- CDN URL (faster): `https://cdn.jsdelivr.net/gh/HttpAnimation/Openlyst-more-builds@main/repo/apps.json`

**Notes:**
- The source includes app permissions (privacy descriptions and entitlements) when available.

---

## F-Droid (Android)

- Repository URL: `https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/fdroid-repo`
- Add this repository in F-Droid client to access OpenLyst Android apps.

---

## Homebrew (macOS/Linux)

### Quick Setup

```bash
brew tap httpanimation/openlyst-more-builds
```

### Installation

```bash
# Add the tap
brew tap httpanimation/openlyst-more-builds https://github.com/HttpAnimation/Openlyst-more-builds.git

# Install apps
brew install httpanimation/openlyst-more-builds/app-name

# For cask applications on macOS
brew install --cask httpanimation/openlyst-more-builds/app-name
```

### Available Commands

| Command | Description |
|---------|-------------|
| `brew update` | Update the tap |
| `brew search httpanimation/openlyst-more-builds/` | List available formulae |
| `brew install httpanimation/openlyst-more-builds/app-name` | Install an application |
| `brew uninstall app-name` | Uninstall an application |
| `brew info httpanimation/openlyst-more-builds/app-name` | Get formula info |

---

## Development

### Requirements

```bash
pip install -r requirements.txt
```

### Project Structure

```
├── build.py                    # Unified build script
├── repo/                       # AltStore repository output
├── fdroid-repo/               # F-Droid repository output
├── homebrew-tap/              # Homebrew tap output
│   └── Formula/               # Homebrew formulae
└── .github/workflows/
    └── build-unified.yml      # Unified GitHub Actions workflow
```
