# AUR Package Updater Setup

This document describes how to set up the automated AUR (Arch User Repository) package updater.

## Overview

The AUR updater automatically fetches the latest version information from the [OpenLyst API](https://openlyst.ink/docs/api) and updates the following AUR packages:

- [`klit-bin`](https://aur.archlinux.org/packages/klit-bin) - Klit e621 client
- [`doudou-bin`](https://aur.archlinux.org/packages/doudou-bin) - Doudou music player
- [`finar-bin`](https://aur.archlinux.org/packages/finar-bin) - Finar Jellyfin client

## GitHub Secrets Configuration

### Required Secret: `AUR_SSH_PRIVATE_KEY`

To push updates to AUR, you need to add your SSH private key as a GitHub secret.

1. Go to your GitHub repository settings
2. Navigate to **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `AUR_SSH_PRIVATE_KEY`
5. Value: Paste the contents of your `id_ed25519` private key

> ⚠️ **Security Note**: Never commit your private key to the repository. Always use GitHub Secrets.

### AUR SSH Key Setup

If you haven't already set up your SSH key on AUR:

1. **Generate a key pair** (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/id_ed25519
   ```

2. **Register your public key on AUR**:
   - Go to https://aur.archlinux.org/login
   - Navigate to "My Account"
   - Paste your public key (`~/.ssh/id_ed25519.pub`) in the SSH Public Key field

3. **Test the connection**:
   ```bash
   ssh -T aur@aur.archlinux.org
   ```

## Workflow Usage

### Automatic Updates

The workflow runs daily at 6:00 AM UTC via cron schedule. It will:

1. Check all packages for new versions via OpenLyst API
2. Download the Linux x86_64 zip and calculate SHA256
3. Generate updated PKGBUILD and .SRCINFO
4. Push changes to AUR

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to **Actions** → **Update AUR Packages**
2. Click **Run workflow**
3. Options:
   - **Package**: Select a specific package or leave empty for all
   - **Force**: Update even if the version hasn't changed
   - **Dry run**: Preview changes without pushing

## Local Usage

You can also run the update script locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Update all packages
python update_aur_packages.py --all

# Update a specific package
python update_aur_packages.py --package klit-bin

# Dry run (preview only)
python update_aur_packages.py --all --dry-run

# Force update
python update_aur_packages.py --package doudou-bin --force

# Verbose output
python update_aur_packages.py --all --verbose
```

## Package Configuration

The packages are configured in `update_aur_packages.py` in the `AUR_PACKAGES` dictionary:

| AUR Package | OpenLyst Slug | Description |
|-------------|---------------|-------------|
| `klit-bin` | `klit` | e621 client |
| `doudou-bin` | `doudou` | Music player |
| `finar-bin` | `finar` | Jellyfin client |

## OpenLyst API Endpoints Used

The updater uses the following API endpoints:

- `GET /api/v1/apps/{slug}/latest` - Fetch latest version info
- Response includes:
  - `version` - Version string
  - `downloads.Linux.zip.x86_64` - Download URL for Linux x86_64 zip

Example API response:
```json
{
  "success": true,
  "data": {
    "version": "6.0.0",
    "downloads": {
      "Linux": {
        "zip": {
          "x86_64": "https://github.com/.../linux-x64.zip"
        }
      }
    }
  }
}
```

## Troubleshooting

### SSH Connection Failed

If you see SSH errors:

1. Verify your SSH key is correctly added to AUR
2. Check that `AUR_SSH_PRIVATE_KEY` secret contains the full private key including headers
3. Ensure the key has proper permissions (if running locally)

### Package Update Failed

If a specific package fails to update:

1. Check the GitHub Actions logs for detailed error messages
2. Verify the OpenLyst API returns valid data for that app
3. Ensure the download URL is accessible
4. Check if the AUR package repository exists

### SHA256 Mismatch

If users report SHA256 mismatch errors:

1. The source file may have changed after the PKGBUILD was generated
2. Re-run the workflow to regenerate with the current file hash

## Adding New Packages

To add a new AUR package:

1. Create the package on AUR first (manually or via web interface)
2. Add the package configuration to `AUR_PACKAGES` in `update_aur_packages.py`:
   ```python
   "newapp-bin": AURPackage(
       name="newapp-bin",
       slug="newapp",  # OpenLyst API slug
       description="Description of the app",
       license="GPL3",
       url="https://gitlab.com/Openlyst/newapp",
       depends=["gtk3"],  # Dependencies
       conflicts=["newapp"],
       provides=["newapp"],
   ),
   ```
3. Push and run the workflow

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── aur.yml              # GitHub Actions workflow
├── aur-docs/
│   └── AUR_SETUP.md             # This documentation
├── update_aur_packages.py       # Main update script
└── requirements.txt             # Python dependencies
```
