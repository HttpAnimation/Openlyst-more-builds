#!/usr/bin/env python3
"""
OpenLyst AUR Package Updater

This script fetches the latest app versions from the OpenLyst API and updates
the corresponding AUR (Arch User Repository) packages.

Usage:
    python update_aur_packages.py --package klit-bin
    python update_aur_packages.py --all
    python update_aur_packages.py --package doudou-bin --dry-run
"""

import os
import sys
import json
import hashlib
import subprocess
import tempfile
import argparse
import logging
import requests
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AURPackage:
    """Configuration for an AUR package"""
    name: str  # AUR package name (e.g., klit-bin)
    slug: str  # OpenLyst API slug (e.g., klit)
    description: str
    license: str
    url: str
    depends: List[str]
    conflicts: List[str]
    provides: List[str]
    
    @property
    def git_url(self) -> str:
        return f"ssh://aur@aur.archlinux.org/{self.name}.git"


# Package configurations - Maps AUR package names to OpenLyst slugs
AUR_PACKAGES = {
    "klit-bin": AURPackage(
        name="klit-bin",
        slug="klit",
        description="The successor to BaoBao. A modern, privacy-focused client for the e621 community. Built with user experience and data protection as top priorities.",
        license="GPL3",
        url="https://gitlab.com/Openlyst/klit",
        depends=["gtk3"],
        conflicts=["klit"],
        provides=["klit"],
    ),
    "doudou-bin": AURPackage(
        name="doudou-bin",
        slug="doudou",
        description="Stream your music with ease and style. Source: https://gitlab.com/Openlyst/doudou",
        license="GPL3",
        url="https://gitlab.com/Openlyst/doudou",
        depends=["gtk3", "libmpv.so", "mpv"],
        conflicts=["doudou"],
        provides=["doudou"],
    ),
    "finar-bin": AURPackage(
        name="finar-bin",
        slug="finar",
        description="A beautiful, modern multi-platform Jellyfin client built with Flutter. Source: https://gitlab.com/Openlyst/finar",
        license="AGPL3",
        url="https://gitlab.com/Openlyst/finar",
        depends=["gtk3", "libmpv.so", "mpv"],
        conflicts=["finar"],
        provides=["finar"],
    ),
}


class OpenLystClient:
    """Client for interacting with OpenLyst API"""
    
    BASE_URL = "https://openlyst.ink/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Openlyst-AUR-Updater/1.0'
        })
    
    def get_latest_version(self, slug: str) -> Optional[Dict]:
        """Fetch the latest version of an app"""
        try:
            url = f"{self.BASE_URL}/apps/{slug}/latest"
            logger.info(f"Fetching latest version from {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data.get('data')
            else:
                logger.error(f"API returned unsuccessful response: {data}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch latest version for {slug}: {e}")
            return None
    
    def get_linux_zip_url(self, version_data: Dict) -> Optional[str]:
        """Extract the Linux x86_64 zip download URL from version data"""
        try:
            downloads = version_data.get('downloads', {})
            linux = downloads.get('Linux', {})
            zip_data = linux.get('zip', {})
            return zip_data.get('x86_64', '')
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to extract Linux zip URL: {e}")
            return None


def calculate_sha256(url: str) -> Optional[str]:
    """Download file and calculate SHA256 hash"""
    try:
        logger.info(f"Downloading {url} to calculate SHA256...")
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
        
        sha256_hash = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=8192):
            sha256_hash.update(chunk)
        
        hash_value = sha256_hash.hexdigest()
        logger.info(f"SHA256: {hash_value}")
        return hash_value
        
    except Exception as e:
        logger.error(f"Failed to calculate SHA256 for {url}: {e}")
        return None


def generate_pkgbuild(package: AURPackage, version: str, download_url: str, sha256: str) -> str:
    """Generate PKGBUILD content for an AUR package"""
    
    # Get the app base name from package name (remove -bin suffix)
    app_name = package.name.replace('-bin', '')
    
    # Format dependencies
    depends_str = ' '.join(f"'{dep}'" for dep in package.depends)
    conflicts_str = ' '.join(f"'{dep}'" for dep in package.conflicts)
    provides_str = ' '.join(f"'{dep}'" for dep in package.provides)
    
    pkgbuild = f'''# Maintainer: HttpAnimations <httpanimations@proton.me>
# Auto-generated by OpenLyst AUR Updater

pkgname={package.name}
pkgver={version}
pkgrel=1
pkgdesc="{package.description}"
arch=('x86_64')
url="{package.url}"
license=('{package.license}')
depends=({depends_str})
conflicts=({conflicts_str})
provides=({provides_str})
source=("${{pkgname}}-${{pkgver}}.zip::{download_url}")
sha256sums=('{sha256}')
options=('!strip')

package() {{
    cd "$srcdir"
    
    # Find the extracted directory (handles different naming patterns)
    local extracted_dir
    extracted_dir=$(find . -maxdepth 1 -type d -name "{app_name}*" | head -1)
    
    if [ -z "$extracted_dir" ]; then
        # Fallback: try to find any directory that's not current/parent
        extracted_dir=$(find . -maxdepth 1 -type d ! -name "." ! -name ".." | head -1)
    fi
    
    if [ -z "$extracted_dir" ]; then
        echo "Error: Could not find extracted directory"
        return 1
    fi
    
    # Install the application
    install -dm755 "$pkgdir/opt/{app_name}"
    cp -r "$extracted_dir"/* "$pkgdir/opt/{app_name}/"
    
    # Make the main executable
    chmod +x "$pkgdir/opt/{app_name}/{app_name}"
    
    # Create symlink in /usr/bin
    install -dm755 "$pkgdir/usr/bin"
    ln -sf "/opt/{app_name}/{app_name}" "$pkgdir/usr/bin/{app_name}"
    
    # Install desktop file if it exists
    if [ -f "$extracted_dir/{app_name}.desktop" ]; then
        install -Dm644 "$extracted_dir/{app_name}.desktop" "$pkgdir/usr/share/applications/{app_name}.desktop"
    else
        # Create a basic desktop file
        install -dm755 "$pkgdir/usr/share/applications"
        cat > "$pkgdir/usr/share/applications/{app_name}.desktop" << EOF
[Desktop Entry]
Type=Application
Name={app_name.capitalize()}
Comment={package.description}
Exec=/opt/{app_name}/{app_name}
Icon={app_name}
Terminal=false
Categories=Utility;
EOF
    fi
    
    # Install icon if it exists
    if [ -f "$extracted_dir/data/flutter_assets/assets/icons/icon.png" ]; then
        install -Dm644 "$extracted_dir/data/flutter_assets/assets/icons/icon.png" \
            "$pkgdir/usr/share/icons/hicolor/256x256/apps/{app_name}.png"
    fi
    
    # Install bundled libraries
    if [ -d "$extracted_dir/lib" ]; then
        install -dm755 "$pkgdir/opt/{app_name}/lib"
        cp -r "$extracted_dir/lib"/* "$pkgdir/opt/{app_name}/lib/"
    fi
}}
'''
    return pkgbuild


def generate_srcinfo(package: AURPackage, version: str, download_url: str, sha256: str) -> str:
    """Generate .SRCINFO content for an AUR package"""
    
    app_name = package.name.replace('-bin', '')
    
    srcinfo = f'''pkgbase = {package.name}
\tpkgdesc = {package.description}
\tpkgver = {version}
\tpkgrel = 1
\turl = {package.url}
\tarch = x86_64
\tlicense = {package.license}
'''
    
    for dep in package.depends:
        srcinfo += f'\tdepends = {dep}\n'
    
    for conflict in package.conflicts:
        srcinfo += f'\tconflicts = {conflict}\n'
    
    for provide in package.provides:
        srcinfo += f'\tprovides = {provide}\n'
    
    srcinfo += f'''\toptions = !strip
\tsource = {package.name}-{version}.zip::{download_url}
\tsha256sums = {sha256}

pkgname = {package.name}
'''
    
    return srcinfo


def setup_ssh_key(ssh_key_path: Optional[str] = None) -> bool:
    """Setup SSH key for AUR authentication"""
    try:
        # Ensure .ssh directory exists
        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        # If SSH key path is provided, copy it
        if ssh_key_path:
            key_dest = ssh_dir / 'aur_ed25519'
            if Path(ssh_key_path).exists():
                with open(ssh_key_path, 'r') as src:
                    content = src.read()
                with open(key_dest, 'w') as dst:
                    dst.write(content)
                os.chmod(key_dest, 0o600)
            else:
                logger.error(f"SSH key not found at {ssh_key_path}")
                return False
        
        # Configure SSH to use the key for AUR
        config_path = ssh_dir / 'config'
        aur_config = '''
Host aur.archlinux.org
    IdentityFile ~/.ssh/aur_ed25519
    User aur
    StrictHostKeyChecking accept-new
'''
        
        # Check if config exists and if AUR entry already present
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing_config = f.read()
            if 'aur.archlinux.org' not in existing_config:
                with open(config_path, 'a') as f:
                    f.write(aur_config)
        else:
            with open(config_path, 'w') as f:
                f.write(aur_config)
            os.chmod(config_path, 0o600)
        
        logger.info("SSH configuration for AUR completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup SSH key: {e}")
        return False


def clone_aur_repo(package_name: str, work_dir: Path) -> Optional[Path]:
    """Clone the AUR repository for a package"""
    try:
        repo_path = work_dir / package_name
        git_url = f"ssh://aur@aur.archlinux.org/{package_name}.git"
        
        logger.info(f"Cloning {git_url}...")
        result = subprocess.run(
            ['git', 'clone', git_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to clone repository: {result.stderr}")
            return None
        
        logger.info(f"Successfully cloned to {repo_path}")
        return repo_path
        
    except subprocess.TimeoutExpired:
        logger.error("Git clone timed out")
        return None
    except Exception as e:
        logger.error(f"Failed to clone AUR repo: {e}")
        return None


def configure_git(repo_path: Path) -> bool:
    """Configure git user for commits"""
    try:
        subprocess.run(
            ['git', 'config', 'user.email', 'httpanimations@proton.me'],
            cwd=repo_path,
            check=True
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'HttpAnimations'],
            cwd=repo_path,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to configure git: {e}")
        return False


def commit_and_push(repo_path: Path, version: str, package_name: str) -> bool:
    """Commit changes and push to AUR"""
    try:
        # Stage all changes
        subprocess.run(['git', 'add', '-A'], cwd=repo_path, check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            logger.info("No changes to commit")
            return True
        
        # Commit
        commit_msg = f"Update {package_name} to version {version}"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=repo_path,
            check=True
        )
        
        # Push
        logger.info("Pushing changes to AUR...")
        result = subprocess.run(
            ['git', 'push', 'origin', 'master'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to push: {result.stderr}")
            return False
        
        logger.info("Successfully pushed changes to AUR")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Git push timed out")
        return False


def get_current_aur_version(repo_path: Path) -> Optional[str]:
    """Read current version from PKGBUILD"""
    try:
        pkgbuild_path = repo_path / 'PKGBUILD'
        if not pkgbuild_path.exists():
            return None
        
        with open(pkgbuild_path, 'r') as f:
            for line in f:
                if line.startswith('pkgver='):
                    return line.strip().split('=')[1]
        return None
    except Exception as e:
        logger.error(f"Failed to read PKGBUILD version: {e}")
        return None


def update_package(package_name: str, dry_run: bool = False, force: bool = False) -> Tuple[bool, str]:
    """Update a single AUR package"""
    
    if package_name not in AUR_PACKAGES:
        return False, f"Unknown package: {package_name}"
    
    package = AUR_PACKAGES[package_name]
    client = OpenLystClient()
    
    # Fetch latest version from OpenLyst API
    logger.info(f"Fetching latest version for {package.slug}...")
    version_data = client.get_latest_version(package.slug)
    
    if not version_data:
        return False, f"Failed to fetch version data for {package.slug}"
    
    version = version_data.get('version')
    if not version:
        return False, "No version found in API response"
    
    logger.info(f"Latest version: {version}")
    
    # Get download URL
    download_url = client.get_linux_zip_url(version_data)
    if not download_url:
        return False, f"No Linux x86_64 zip download URL found for {package.slug}"
    
    logger.info(f"Download URL: {download_url}")
    
    # Calculate SHA256
    sha256 = calculate_sha256(download_url)
    if not sha256:
        return False, "Failed to calculate SHA256 hash"
    
    if dry_run:
        logger.info("=== DRY RUN - Would generate: ===")
        pkgbuild = generate_pkgbuild(package, version, download_url, sha256)
        print(pkgbuild)
        return True, f"Dry run completed for {package_name} v{version}"
    
    # Clone AUR repository
    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)
        repo_path = clone_aur_repo(package_name, work_dir)
        
        if not repo_path:
            return False, "Failed to clone AUR repository"
        
        # Check current version
        current_version = get_current_aur_version(repo_path)
        if current_version == version and not force:
            return True, f"{package_name} is already at version {version}"
        
        logger.info(f"Updating {package_name} from {current_version} to {version}")
        
        # Configure git
        if not configure_git(repo_path):
            return False, "Failed to configure git"
        
        # Generate and write PKGBUILD
        pkgbuild_content = generate_pkgbuild(package, version, download_url, sha256)
        pkgbuild_path = repo_path / 'PKGBUILD'
        with open(pkgbuild_path, 'w') as f:
            f.write(pkgbuild_content)
        logger.info(f"Written PKGBUILD to {pkgbuild_path}")
        
        # Generate and write .SRCINFO
        srcinfo_content = generate_srcinfo(package, version, download_url, sha256)
        srcinfo_path = repo_path / '.SRCINFO'
        with open(srcinfo_path, 'w') as f:
            f.write(srcinfo_content)
        logger.info(f"Written .SRCINFO to {srcinfo_path}")
        
        # Commit and push
        if not commit_and_push(repo_path, version, package_name):
            return False, "Failed to push changes to AUR"
    
    return True, f"Successfully updated {package_name} to version {version}"


def main():
    parser = argparse.ArgumentParser(
        description='Update AUR packages from OpenLyst API'
    )
    parser.add_argument(
        '--package', '-p',
        type=str,
        help='Package name to update (e.g., klit-bin, doudou-bin, finar-bin)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Update all packages'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force update even if version is the same'
    )
    parser.add_argument(
        '--ssh-key',
        type=str,
        help='Path to SSH private key for AUR authentication'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Setup SSH key if provided
    if args.ssh_key:
        if not setup_ssh_key(args.ssh_key):
            logger.error("Failed to setup SSH key")
            sys.exit(1)
    
    # Determine which packages to update
    if args.all:
        packages = list(AUR_PACKAGES.keys())
    elif args.package:
        packages = [args.package]
    else:
        parser.print_help()
        sys.exit(1)
    
    # Update packages
    results = []
    for package_name in packages:
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing {package_name}")
        logger.info(f"{'='*50}")
        
        success, message = update_package(
            package_name,
            dry_run=args.dry_run,
            force=args.force
        )
        results.append((package_name, success, message))
        logger.info(f"Result: {message}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    success_count = 0
    for package_name, success, message in results:
        status = "✓" if success else "✗"
        print(f"  {status} {package_name}: {message}")
        if success:
            success_count += 1
    
    print(f"\nTotal: {success_count}/{len(results)} packages updated successfully")
    
    # Exit with error if any package failed
    if success_count < len(results):
        sys.exit(1)


if __name__ == '__main__':
    main()
