# Openlyst Homebrew Tap

This is a Homebrew tap for macOS and Linux applications from [OpenLyst](https://openlyst.ink).

## Installation

First, add this tap to your Homebrew:

```bash
brew tap httpanimation/openlyst-more-builds https://github.com/HttpAnimation/Openlyst-more-builds.git
```

Then install any available formula:

```bash
brew install httpanimation/openlyst-more-builds/app-name
```

Or for cask applications on macOS:

```bash
brew install --cask httpanimation/openlyst-more-builds/app-name
```

## Available Formulae

The formulae are automatically generated from the OpenLyst API. Check the `Formula/` directory for available applications.

## Usage

Once installed, you can:

- Update the tap: `brew update`
- List available formulae: `brew search httpanimation/openlyst-more-builds/`
- Install an application: `brew install httpanimation/openlyst-more-builds/app-name`
- Uninstall an application: `brew uninstall app-name`

## Automated Updates

The formulae in this tap are automatically updated via GitHub Actions when the "Build Homebrew Tap" workflow runs.