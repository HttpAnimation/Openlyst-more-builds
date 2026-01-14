This project provides builds for Openlyst projects

https://openlyst.ink

## AltStore (iOS)

- Add this Source URL in AltStore: https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/repo/apps.json
- If Raw is slow (pause), use CDN: https://cdn.jsdelivr.net/gh/HttpAnimation/Openlyst-more-builds@main/repo/apps.json
- To refresh the source, run the "Build AltStore Repository" workflow in GitHub Actions.

Notes
- The source includes app permissions (privacy descriptions and entitlements) when available.

## Homebrew (macOS/Linux)

### Installation

First, add this tap to your Homebrew:

```bash
brew tap httpanimation/openlyst-more-builds https://github.com/HttpAnimation/Openlyst-more-builds.git
```

Then install any available formula:

```bash
# For regular formulae
brew install httpanimation/openlyst-more-builds/app-name

# For cask applications on macOS
brew install --cask httpanimation/openlyst-more-builds/app-name
```

### Available Commands

- **Update the tap**: `brew update`
- **List available formulae**: `brew search httpanimation/openlyst-more-builds/`
- **Install an application**: `brew install httpanimation/openlyst-more-builds/app-name`
- **Uninstall an application**: `brew uninstall app-name`
- **Get formula info**: `brew info httpanimation/openlyst-more-builds/app-name`

### Automated Updates

- Formulae are automatically updated daily via GitHub Actions
- Manual updates can be triggered via the "Build Homebrew Tap" workflow
- To refresh the tap: run the "Build Homebrew Tap" workflow in GitHub Actions
