#!/usr/bin/env python3
# ============================================================================
# Setup Script - Copy Data Files to Dashboard
# ============================================================================
"""
Helper script to copy enrichment CSV files to the dashboard data folder.

Usage:
    python setup_data.py
"""

import os
import shutil
from pathlib import Path


def main():
    """Copy CSV files from various locations to the data folder"""
    
    print("🔍 Searching for enrichment CSV files...\n")
    
    # Define source directories to search
    source_dirs = [
        "../Code/Output-Summary-Data",
        "../Data/Chicago/Segmented-Data",
        "../Data/Napa/Segmented-Data",
        "../Data"
    ]
    
    # Target directory
    target_dir = Path("data")
    target_dir.mkdir(exist_ok=True)
    
    files_found = []
    
    # Search for CSV and Excel files
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            continue
        
        # Find CSV files
        csv_files = list(source_path.glob("*.csv"))
        excel_files = list(source_path.glob("*.xlsx"))
        
        files_found.extend(csv_files)
        files_found.extend(excel_files)
    
    if not files_found:
        print("❌ No CSV or Excel files found in search directories")
        print("\nSearched in:")
        for d in source_dirs:
            print(f"  - {d}")
        print("\n💡 Please manually copy your CSV files to Webtool/data/")
        return
    
    print(f"✅ Found {len(files_found)} file(s):\n")
    
    # Display files and ask for confirmation
    for i, file_path in enumerate(files_found, 1):
        size_kb = file_path.stat().st_size / 1024
        print(f"{i:2d}. {file_path.name:50s} ({size_kb:.1f} KB) - {file_path.parent}")
    
    print("\n" + "="*80)
    print("Would you like to copy these files to Webtool/data/?")
    print("="*80)
    
    # Interactive options
    print("\nOptions:")
    print("  [A] Copy ALL files")
    print("  [S] Select specific files (comma-separated numbers)")
    print("  [N] Cancel")
    
    choice = input("\nYour choice: ").strip().upper()
    
    if choice == 'N':
        print("\n❌ Cancelled. No files copied.")
        return
    
    # Determine which files to copy
    if choice == 'A':
        files_to_copy = files_found
    elif choice == 'S':
        try:
            indices = [int(x.strip()) for x in input("Enter file numbers (e.g., 1,3,5): ").split(',')]
            files_to_copy = [files_found[i-1] for i in indices if 1 <= i <= len(files_found)]
        except (ValueError, IndexError):
            print("\n❌ Invalid input. Cancelled.")
            return
    else:
        print("\n❌ Invalid choice. Cancelled.")
        return
    
    # Copy files
    print("\n📦 Copying files...\n")
    copied_count = 0
    
    for file_path in files_to_copy:
        target_path = target_dir / file_path.name
        
        # Check if file already exists
        if target_path.exists():
            print(f"⚠️  Skipping {file_path.name} (already exists)")
            continue
        
        try:
            shutil.copy2(file_path, target_path)
            print(f"✅ Copied {file_path.name}")
            copied_count += 1
        except Exception as e:
            print(f"❌ Error copying {file_path.name}: {e}")
    
    print("\n" + "="*80)
    print(f"✅ Successfully copied {copied_count} file(s) to Webtool/data/")
    print("="*80)
    
    print("\n🚀 Next step: Run the dashboard with:")
    print("   streamlit run app.py")


if __name__ == "__main__":
    main()


