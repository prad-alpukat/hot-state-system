#!/usr/bin/env python3
"""
Build script untuk Hot Stage System
Jalankan di Windows untuk menghasilkan .exe
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Hapus folder build sebelumnya"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}/")

    # Remove .spec file
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"Removed {spec_file}")


def build_exe():
    """Build executable dengan PyInstaller"""

    # PyInstaller command
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name=HotStageSystem',
        '--onedir',  # Folder dengan semua dependencies
        '--windowed',  # No console window
        '--noconfirm',  # Overwrite tanpa konfirmasi

        # Add data files
        '--add-data=src;src',

        # Hidden imports yang mungkin tidak terdeteksi
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        '--hidden-import=PySide6.QtSvg',
        '--hidden-import=pyqtgraph',
        '--hidden-import=numpy',
        '--hidden-import=cv2',

        # Collect semua data dari packages
        '--collect-data=pyqtgraph',

        # Entry point
        'main.py'
    ]

    # Adjust path separator untuk Windows
    if sys.platform == 'win32':
        cmd = [c.replace(';', os.pathsep) if ';' in c else c for c in cmd]

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
        print(f"\nExecutable location: dist/HotStageSystem/")
        print("Run: dist/HotStageSystem/HotStageSystem.exe")
    else:
        print("\n" + "="*50)
        print("BUILD FAILED!")
        print("="*50)
        sys.exit(1)


def create_installer():
    """Buat installer dengan NSIS (opsional, untuk Windows)"""
    # TODO: Implement NSIS installer creation
    pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Build Hot Stage System')
    parser.add_argument('--clean', action='store_true', help='Clean build files')
    parser.add_argument('--build', action='store_true', help='Build executable')

    args = parser.parse_args()

    if args.clean:
        clean_build()
    elif args.build:
        build_exe()
    else:
        # Default: clean and build
        clean_build()
        build_exe()


if __name__ == '__main__':
    main()
