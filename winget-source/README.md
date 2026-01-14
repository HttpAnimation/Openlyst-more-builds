# OpenLyst Winget Source

This is a REST API source for Winget that allows you to install Windows applications from [OpenLyst](https://openlyst.ink) using the Windows Package Manager.

## Quick Setup

Add this source to Winget:

```powershell
winget source add openlyst https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/winget-source/information.json
```

## Installation

After adding the source, install packages:

```powershell
# Install from OpenLyst source
winget install OpenLyst.Docan --source openlyst

# Search in OpenLyst source  
winget search --source openlyst

# List all packages from OpenLyst
winget search OpenLyst. --source openlyst
```

## API Endpoints

This source provides the following REST API endpoints that Winget uses:

- `/information.json` - Source metadata and capabilities
- `/packageManifests.json` - Search and package listing
- `/packages.json` - Detailed package information
- `/packages/{PackageIdentifier}.json` - Individual package manifests

## Source Information

- **Source Name**: OpenLyst
- **Source Identifier**: OpenLyst  
- **Supported Versions**: 1.4.0, 1.5.0
- **Package Namespace**: OpenLyst.*

## Available Packages

All packages use the `OpenLyst.` prefix:

- `OpenLyst.Docan` - Universal AI chat application
- `OpenLyst.Doudou` - Music player for self-hosted services
- `OpenLyst.Finar` - Finance management application
- `OpenLyst.Klit` - Text editor and IDE
- `OpenLyst.Opentorrent` - Torrent client

## Usage Examples

```powershell
# Add source (one-time setup)
winget source add openlyst https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/winget-source/information.json

# Search for applications
winget search --source openlyst

# Install specific application
winget install OpenLyst.Docan --source openlyst

# Get package information
winget show OpenLyst.Docan --source openlyst

# Upgrade packages from this source
winget upgrade --source openlyst

# Remove the source
winget source remove openlyst
```

## Benefits of Using a Source

- **Easy installation**: Simple `winget install` commands
- **Automatic updates**: Winget can manage updates
- **Source isolation**: Packages are clearly identified as from OpenLyst
- **Better search**: Native Winget search integration
- **Dependency management**: Winget handles dependencies

## Technical Details

This source follows the [Microsoft Winget REST source specification](https://github.com/microsoft/winget-cli-restsource) and provides:

- Package search and filtering
- Version management
- Installer metadata with SHA256 hashes
- Multi-architecture support (x64, ARM64)
- Multiple installer types (EXE, MSI, MSIX, ZIP)

## Automated Updates

The source is automatically updated via GitHub Actions when the "Build Winget Source" workflow runs, ensuring packages are always current with the OpenLyst API.