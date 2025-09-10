#!/usr/bin/env python3
"""
License compliance checker for SQL Genius AI
Ensures all dependencies use approved licenses
"""

import json
import sys
from typing import Set, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Approved licenses (add more as needed)
APPROVED_LICENSES: Set[str] = {
    'MIT License',
    'MIT',
    'BSD License',
    'BSD',
    'BSD-3-Clause',
    'BSD-2-Clause', 
    'Apache Software License',
    'Apache License 2.0',
    'Apache 2.0',
    'Python Software Foundation License',
    'PSF',
    'Mozilla Public License 2.0 (MPL 2.0)',
    'MPL-2.0',
    'ISC License',
    'ISC',
    'Zlib/Libpng License',
    'zlib/libpng',
    'The Unlicense',
    'Public Domain',
    'CC0 1.0 Universal (CC0 1.0) Public Domain Dedication'
}

# Licenses that require special attention (copyleft)
COPYLEFT_LICENSES: Set[str] = {
    'GNU General Public License v2 (GPLv2)',
    'GNU General Public License v3 (GPLv3)',
    'GNU Lesser General Public License v2.1 (LGPLv2.1)',
    'GNU Lesser General Public License v3 (LGPLv3)',
    'GNU Affero General Public License v3 (AGPLv3)',
    'GPL',
    'LGPL',
    'AGPL',
    'Copyleft'
}

# Explicitly forbidden licenses
FORBIDDEN_LICENSES: Set[str] = {
    'UNKNOWN',
    'UNLICENSED',
    'Proprietary',
    'Commercial'
}

# Known packages with valid licenses that sometimes show as UNKNOWN
PACKAGE_LICENSE_WHITELIST: Dict[str, str] = {
    'attrs': 'MIT License',
    'humanize': 'MIT License',
    'jsonschema': 'MIT License',
    'jsonschema-specifications': 'MIT License',
    'mypy_extensions': 'MIT License',
    'mypy-extensions': 'MIT License',
    'referencing': 'MIT License',
    'regex': 'Apache Software License',
    'typing_extensions': 'Python Software Foundation License',
    'typing-extensions': 'Python Software Foundation License',
    'urllib3': 'MIT License',
    'zipp': 'MIT License'
}

def load_licenses(file_path: str = 'licenses.json') -> List[Dict]:
    """Load license information from pip-licenses output"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"License file {file_path} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        sys.exit(1)

def normalize_license(license_name: str) -> str:
    """Normalize license name for comparison"""
    if not license_name:
        return 'UNKNOWN'
    
    # Handle common variations
    license_name = license_name.strip()
    
    # Common mappings
    mappings = {
        'Apache': 'Apache Software License',
        'Apache-2.0': 'Apache Software License',
        'BSD-3': 'BSD-3-Clause',
        'BSD-2': 'BSD-2-Clause',
        'MIT-License': 'MIT License',
        'Mozilla Public License 2.0': 'MPL-2.0',
        'ISC License (ISCL)': 'ISC License'
    }
    
    return mappings.get(license_name, license_name)

def categorize_license(license_name: str) -> str:
    """Categorize license as approved, copyleft, or forbidden"""
    normalized = normalize_license(license_name)
    
    if normalized in APPROVED_LICENSES:
        return 'approved'
    elif normalized in COPYLEFT_LICENSES:
        return 'copyleft'
    elif normalized in FORBIDDEN_LICENSES:
        return 'forbidden'
    else:
        return 'unknown'

def check_license_compliance(licenses: List[Dict]) -> Dict[str, List[Dict]]:
    """Check license compliance and categorize packages"""
    results = {
        'approved': [],
        'copyleft': [],
        'forbidden': [],
        'unknown': []
    }
    
    for package in licenses:
        package_name = package.get('Name', 'Unknown')
        license_name = package.get('License', 'UNKNOWN')
        version = package.get('Version', 'Unknown')
        
        # Check if package is in whitelist
        if package_name in PACKAGE_LICENSE_WHITELIST:
            # Use the known license from whitelist
            license_name = PACKAGE_LICENSE_WHITELIST[package_name]
            category = 'approved'  # All whitelisted packages are approved
        else:
            category = categorize_license(license_name)
        
        results[category].append({
            'name': package_name,
            'version': version,
            'license': license_name,
            'normalized_license': normalize_license(license_name)
        })
    
    return results

def generate_compliance_report(results: Dict[str, List[Dict]]) -> None:
    """Generate detailed compliance report"""
    print("\n" + "="*60)
    print("LICENSE COMPLIANCE REPORT")
    print("="*60)
    
    total_packages = sum(len(packages) for packages in results.values())
    print(f"Total packages analyzed: {total_packages}")
    
    # Approved licenses
    approved_count = len(results['approved'])
    print(f"\nAPPROVED LICENSES ({approved_count} packages):")
    for package in sorted(results['approved'], key=lambda x: x['name']):
        print(f"  - {package['name']} ({package['version']}): {package['license']}")
    
    # Copyleft licenses (require attention)
    copyleft_count = len(results['copyleft'])
    if copyleft_count > 0:
        print(f"\nCOPYLEFT LICENSES ({copyleft_count} packages) - REVIEW REQUIRED:")
        for package in sorted(results['copyleft'], key=lambda x: x['name']):
            print(f"  - {package['name']} ({package['version']}): {package['license']}")
        print("\n  NOTE: Copyleft licenses may require special handling for commercial use.")
    
    # Unknown licenses
    unknown_count = len(results['unknown'])
    if unknown_count > 0:
        print(f"\nUNKNOWN LICENSES ({unknown_count} packages) - REVIEW REQUIRED:")
        for package in sorted(results['unknown'], key=lambda x: x['name']):
            print(f"  - {package['name']} ({package['version']}): {package['license']}")
        print("\n  ACTION: Review these licenses manually and update the approved list.")
    
    # Forbidden licenses
    forbidden_count = len(results['forbidden'])
    if forbidden_count > 0:
        print(f"\nFORBIDDEN LICENSES ({forbidden_count} packages) - ACTION REQUIRED:")
        for package in sorted(results['forbidden'], key=lambda x: x['name']):
            print(f"  - {package['name']} ({package['version']}): {package['license']}")
        print("\n  ACTION: Remove these packages or find alternatives with approved licenses.")
    
    # Summary
    print(f"\n" + "-"*60)
    print("SUMMARY:")
    print(f"  Approved:  {approved_count:3d} packages")
    print(f"  Copyleft:  {copyleft_count:3d} packages (review required)")
    print(f"  Unknown:   {unknown_count:3d} packages (review required)")
    print(f"  Forbidden: {forbidden_count:3d} packages (action required)")
    print("-"*60)

def generate_license_matrix() -> None:
    """Generate license compatibility matrix"""
    print("\n" + "="*60)
    print("LICENSE COMPATIBILITY MATRIX")
    print("="*60)
    
    print("\nAPPROVED FOR COMMERCIAL USE:")
    for license_name in sorted(APPROVED_LICENSES):
        print(f"  - {license_name}")
    
    print("\nCOPYLEFT (Special Handling Required):")
    for license_name in sorted(COPYLEFT_LICENSES):
        print(f"  - {license_name}")
    
    print("\nFORBIDDEN:")
    for license_name in sorted(FORBIDDEN_LICENSES):
        print(f"  - {license_name}")

def export_results(results: Dict[str, List[Dict]], output_file: str = 'license_compliance_report.json') -> None:
    """Export results to JSON file for CI/CD pipeline"""
    summary = {
        'total_packages': sum(len(packages) for packages in results.values()),
        'approved_count': len(results['approved']),
        'copyleft_count': len(results['copyleft']),
        'unknown_count': len(results['unknown']),
        'forbidden_count': len(results['forbidden']),
        'compliance_status': 'PASS' if len(results['forbidden']) == 0 else 'FAIL',
        'packages': results,
        'timestamp': json.dumps(None, default=str)  # Will be set by JSON encoder
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"Compliance report exported to {output_file}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check license compliance for SQL Genius AI')
    parser.add_argument('--input', '-i', default='licenses.json', 
                       help='Input license file (default: licenses.json)')
    parser.add_argument('--output', '-o', default='license_compliance_report.json',
                       help='Output compliance report (default: license_compliance_report.json)')
    parser.add_argument('--matrix', action='store_true',
                       help='Show license compatibility matrix')
    parser.add_argument('--fail-on-forbidden', action='store_true', default=True,
                       help='Fail if forbidden licenses are found (default: True)')
    parser.add_argument('--fail-on-unknown', action='store_true',
                       help='Fail if unknown licenses are found')
    
    args = parser.parse_args()
    
    if args.matrix:
        generate_license_matrix()
        return
    
    # Load and analyze licenses
    logger.info(f"Loading licenses from {args.input}")
    licenses = load_licenses(args.input)
    
    logger.info(f"Analyzing {len(licenses)} packages")
    results = check_license_compliance(licenses)
    
    # Generate report
    generate_compliance_report(results)
    
    # Export results
    export_results(results, args.output)
    
    # Check compliance status
    exit_code = 0
    
    if args.fail_on_forbidden and len(results['forbidden']) > 0:
        logger.error(f"Found {len(results['forbidden'])} packages with forbidden licenses")
        exit_code = 1
    
    if args.fail_on_unknown and len(results['unknown']) > 0:
        logger.error(f"Found {len(results['unknown'])} packages with unknown licenses")
        exit_code = 1
    
    if len(results['copyleft']) > 0:
        logger.warning(f"Found {len(results['copyleft'])} packages with copyleft licenses - review required")
    
    if exit_code == 0:
        logger.info("License compliance check PASSED")
    else:
        logger.error("License compliance check FAILED")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()