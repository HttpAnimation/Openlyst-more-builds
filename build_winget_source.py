#!/usr/bin/env python3
"""
OpenLyst Winget REST Source

This script creates a REST API-compatible source for Winget that can be hosted
and added as a custom source using: winget source add openlyst <URL>
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import hashlib
import re
from urllib.parse import urljoin, urlparse
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenLystClient:
    """Client for interacting with OpenLyst API"""
    
    BASE_URL = "https://openlyst.ink/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Openlyst-Winget-Source/1.0'
        })
    
    def get_all_apps(self, platform: str = "Windows", lang: str = "en") -> List[Dict]:
        """Fetch all Windows apps from OpenLyst"""
        try:
            url = f"{self.BASE_URL}/apps"
            params = {
                'platform': platform,
                'lang': lang,
                'filter': 'active'
            }
            
            logger.info(f"Fetching apps from {url} for platform {platform}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                apps = data.get('data', [])
                logger.info(f"Successfully fetched {len(apps)} apps")
                return apps
            else:
                logger.error(f"API returned unsuccessful response: {data}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch apps: {e}")
            return []
    
    def get_app_versions(self, slug: str, lang: str = "en") -> List[Dict]:
        """Fetch all versions of a specific app"""
        try:
            url = f"{self.BASE_URL}/apps/{slug}/versions"
            params = {'lang': lang}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                versions = data.get('data', [])
                logger.debug(f"Fetched {len(versions) if isinstance(versions, list) else '?'} versions for {slug}")
                return versions if isinstance(versions, list) else []
            return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch app versions for {slug}: {e}")
            return []


class WingetRESTSourceGenerator:
    """Generator for Winget REST source from OpenLyst app data"""
    
    def __init__(self, output_dir: Path, base_url: str):
        self.output_dir = output_dir
        self.base_url = base_url.rstrip('/')
        self.packages_dir = output_dir / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_package_id(self, name: str, publisher: str = "OpenLyst") -> str:
        """Create a valid Winget package identifier"""
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.title())
        clean_publisher = re.sub(r'[^a-zA-Z0-9]', '', publisher)
        return f"{clean_publisher}.{clean_name}"
    
    def get_windows_download_url(self, version: Dict) -> Optional[str]:
        """Extract Windows download URL from version data"""
        downloads = version.get('downloads', {})
        windows_downloads = downloads.get('Windows', {})
        
        if not windows_downloads:
            return None
        
        # Priority order for Windows package types
        for package_type in ['exe', 'msi', 'msix', 'zip']:
            if package_type in windows_downloads:
                pkg_data = windows_downloads[package_type]
                if isinstance(pkg_data, dict):
                    for arch in ['x86_64', 'arm64']:
                        if arch in pkg_data and pkg_data[arch]:
                            return pkg_data[arch]
                elif isinstance(pkg_data, str) and pkg_data.startswith('http'):
                    return pkg_data
        
        return None
    
    def get_file_sha256(self, url: str) -> Optional[str]:
        """Calculate SHA256 hash of download file"""
        try:
            logger.info(f"Calculating SHA256 for {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            sha256_hash = hashlib.sha256(response.content).hexdigest().upper()
            return sha256_hash
        except Exception as e:
            logger.warning(f"Failed to calculate SHA256 for {url}: {e}")
            return None
    
    def determine_installer_type(self, download_url: str) -> str:
        """Determine installer type from URL"""
        url_path = urlparse(download_url).path.lower()
        
        if url_path.endswith('.msi'):
            return 'msi'
        elif url_path.endswith('.msix'):
            return 'msix'
        elif url_path.endswith('.exe'):
            return 'exe'
        elif url_path.endswith('.zip'):
            return 'zip'
        else:
            return 'exe'
    
    def create_package_data(self, app: Dict, version: Dict, package_id: str, calculate_hash: bool = False) -> Dict:
        """Create package data for REST API"""
        download_url = self.get_windows_download_url(version)
        
        if not download_url:
            raise ValueError(f"No Windows download URL found for {app['name']}")
        
        installer_type = self.determine_installer_type(download_url)
        
        # Calculate file hash if requested
        installer_sha256 = None
        if calculate_hash:
            installer_sha256 = self.get_file_sha256(download_url)
        
        package_data = {
            "PackageIdentifier": package_id,
            "PackageName": app['name'],
            "Publisher": "OpenLyst",
            "PublisherUrl": "https://openlyst.ink",
            "PackageUrl": "https://openlyst.ink",
            "License": "Open Source",
            "LicenseUrl": "https://openlyst.ink",
            "ShortDescription": app.get('subtitle', app['name']),
            "Description": app.get('localizedDescription', app.get('subtitle', app['name'])),
            "Tags": ["opensource", "free", "openlyst"],
            "Versions": [
                {
                    "PackageVersion": version['version'],
                    "DefaultLocale": {
                        "PackageLocale": "en-US",
                        "Publisher": "OpenLyst",
                        "PackageName": app['name'],
                        "License": "Open Source",
                        "ShortDescription": app.get('subtitle', app['name']),
                        "Description": app.get('localizedDescription', app.get('subtitle', app['name']))
                    },
                    "Installers": [
                        {
                            "Architecture": "x64",
                            "InstallerType": installer_type,
                            "InstallerUrl": download_url,
                            "InstallerSha256": installer_sha256,
                            "Scope": "user"
                        }
                    ]
                }
            ]
        }
        
        # Remove None values
        if not installer_sha256:
            del package_data["Versions"][0]["Installers"][0]["InstallerSha256"]
        
        return package_data
    
    def generate_source_information(self) -> Dict:
        """Generate source information for Winget"""
        return {
            "Data": {
                "SourceIdentifier": "OpenLyst",
                "ServerSupportedVersions": ["1.4.0", "1.5.0"],
                "SourceName": "OpenLyst",
                "SourceAgreements": {
                    "AgreementsIdentifier": "OpenLyst_1.0",
                    "AgreementLabel": "OpenLyst Terms",
                    "Agreement": "By using this source, you agree to the OpenLyst terms of service.",
                    "AgreementUrl": "https://openlyst.ink"
                },
                "UnsupportedPackageMatchFields": [],
                "RequiredPackageMatchFields": [],
                "UnsupportedQueryParameters": []
            }
        }
    
    def generate_package_manifests(self, app: Dict, versions: List[Dict], calculate_hash: bool = False) -> Optional[Dict]:
        """Generate package manifests for an app"""
        if not versions:
            logger.warning(f"No versions found for app {app.get('name', 'Unknown')}")
            return None
        
        # Use the latest version
        latest_version = versions[0]
        
        # Check if this app supports Windows platform
        app_platforms = latest_version.get('platforms', [])
        if 'Windows' not in app_platforms:
            logger.info(f"App {app.get('name', 'Unknown')} does not support Windows platform")
            return None
        
        try:
            package_id = self.sanitize_package_id(app['name'])
            package_data = self.create_package_data(app, latest_version, package_id, calculate_hash)
            
            # Save individual package file
            package_file = self.packages_dir / f"{package_id}.json"
            with open(package_file, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, indent=2)
            
            logger.info(f"Generated package manifest for {app['name']}: {package_file}")
            return package_data
            
        except ValueError as e:
            logger.warning(f"Skipping {app.get('name', 'Unknown')}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate package manifest for {app.get('name', 'Unknown')}: {e}")
            return None
    
    def generate_search_endpoint(self, packages: List[Dict]) -> Dict:
        """Generate search endpoint response"""
        return {
            "Data": [
                {
                    "PackageIdentifier": pkg["PackageIdentifier"],
                    "PackageName": pkg["PackageName"],
                    "Publisher": pkg["Publisher"],
                    "Versions": [v["PackageVersion"] for v in pkg["Versions"]]
                }
                for pkg in packages
            ]
        }
    
    def generate_packages_endpoint(self, packages: List[Dict]) -> Dict:
        """Generate packages endpoint response"""
        return {
            "Data": packages
        }


def main():
    parser = argparse.ArgumentParser(description='Build Winget REST source from OpenLyst API')
    parser.add_argument('--output-dir', type=str, default='winget-source',
                       help='Output directory for Winget REST source')
    parser.add_argument('--base-url', type=str, 
                       default='https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/winget-source',
                       help='Base URL where the source will be hosted')
    parser.add_argument('--calculate-hash', action='store_true',
                       help='Calculate SHA256 hashes for installers (slower but required)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output_dir = Path(args.output_dir)
    client = OpenLystClient()
    generator = WingetRESTSourceGenerator(output_dir, args.base_url)
    
    logger.info(f"Building Winget REST source for Windows platform in {output_dir}")
    
    # Fetch Windows apps
    apps = client.get_all_apps(platform="Windows")
    if not apps:
        logger.error("No Windows apps found or failed to fetch apps")
        return 1
    
    logger.info(f"Found {len(apps)} Windows apps")
    
    # Generate package manifests
    generated_count = 0
    failed_count = 0
    packages = []
    
    for app in apps:
        slug = app.get('slug')
        if not slug:
            logger.warning(f"No slug found for app: {app}")
            failed_count += 1
            continue
        
        # Get versions for this app
        versions = client.get_app_versions(slug)
        
        package_data = generator.generate_package_manifests(app, versions, args.calculate_hash)
        if package_data:
            packages.append(package_data)
            generated_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Package generation complete: {generated_count} successful, {failed_count} failed")
    
    if packages:
        # Generate source information
        source_info = generator.generate_source_information()
        with open(output_dir / "information.json", 'w', encoding='utf-8') as f:
            json.dump(source_info, f, indent=2)
        
        # Generate search endpoint
        search_data = generator.generate_search_endpoint(packages)
        with open(output_dir / "packageManifests.json", 'w', encoding='utf-8') as f:
            json.dump(search_data, f, indent=2)
        
        # Generate packages endpoint  
        packages_data = generator.generate_packages_endpoint(packages)
        with open(output_dir / "packages.json", 'w', encoding='utf-8') as f:
            json.dump(packages_data, f, indent=2)
        
        logger.info("Generated REST source endpoints")
    
    # Generate source info file
    source_info_file = {
        "name": "OpenLyst Winget REST Source",
        "description": "REST API source for Winget to install Windows applications from OpenLyst",
        "homepage": "https://openlyst.ink",
        "generated_at": datetime.now().isoformat() + "Z",
        "base_url": args.base_url,
        "package_count": generated_count,
        "usage": f"winget source add openlyst {args.base_url}"
    }
    
    with open(output_dir / "source-info.json", 'w', encoding='utf-8') as f:
        json.dump(source_info_file, f, indent=2)
    
    logger.info(f"Generated source info: {output_dir / 'source-info.json'}")
    
    # Only exit with error if NO packages were generated
    if generated_count == 0:
        logger.error("No packages were generated - this indicates a serious problem")
        return 1
    elif failed_count > 0:
        logger.warning(f"{failed_count} apps failed to generate packages, but {generated_count} succeeded")
        return 0
    
    return 0


if __name__ == "__main__":
    exit(main())