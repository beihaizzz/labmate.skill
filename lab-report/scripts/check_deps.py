#!/usr/bin/env python3
"""Dependency pre-flight check for lab-report skill."""

import subprocess
import sys
import json
import shutil
import argparse

def check_uv():
    """Check if uv is installed."""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except FileNotFoundError:
        return False, None

def check_python():
    """Check Python version >= 3.10."""
    version = sys.version_info
    ok = version.major >= 3 and version.minor >= 10
    return ok, f"{version.major}.{version.minor}.{version.micro}"

def check_package(package_name, import_name=None):
    """Check if a package can be imported via uv."""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return True, "available"
    except ImportError:
        return False, "not installed"

def main():
    parser = argparse.ArgumentParser(description='Check lab-report dependencies')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    args = parser.parse_args()

    checks = {
        'uv': check_uv(),
        'python': check_python(),
        'pdfplumber': check_package('pdfplumber'),
        'python-docx': check_package('docx', 'docx'),
        'docxtpl': check_package('docxtpl'),
        'python-pptx': check_package('pptx', 'pptx'),
        'libreoffice': (shutil.which('soffice') is not None or
                        shutil.which('libreoffice') is not None,
                        'available' if (shutil.which('soffice') or shutil.which('libreoffice'))
                        else 'not found (.doc conversion unavailable)'),
    }

    if args.json:
        output = {name: {'ok': ok, 'detail': detail} for name, (ok, detail) in checks.items()}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print("Lab-Report Dependency Check")
        print("=" * 40)
        for name, (ok, detail) in checks.items():
            status = "✅" if ok else ("⚠️" if name == 'libreoffice' else "❌")
            print(f"{status} {name}: {detail or ('OK' if ok else 'MISSING')}")

    all_ok = all(ok for ok, _ in checks.values())
    sys.exit(0 if all_ok else 1)

if __name__ == '__main__':
    main()