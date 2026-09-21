import argparse
import os
import shutil


FILE_CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx"},
    "Code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".html", ".css", ".json", ".xml"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "Executables": {".exe", ".msi", ".dmg", ".apk"},
    "Spreadsheets": {".csv", ".ods"},
}

GENERATED_FOLDERS = set(FILE_CATEGORIES) | {"Others"}


def _unique_destination(path):
    """Return a non-conflicting destination path."""
    if not os.path.exists(path):
        return path

    directory, filename = os.path.split(path)
    stem, extension = os.path.splitext(filename)
    counter = 1
    candidate = os.path.join(directory, f"{stem}_{counter}{extension}")

    while os.path.exists(candidate):
        counter += 1
        candidate = os.path.join(directory, f"{stem}_{counter}{extension}")

    return candidate


def _detect_category(filename):
    """Return the category name for a filename based on its extension."""
    extension = os.path.splitext(filename)[1].lower()
    if not extension:
        return "Others"

    for category, extensions in FILE_CATEGORIES.items():
        if extension in extensions:
            return category

    return "Others"


def organize(folder, recursive=False, dry_run=False):
    """Organize files in *folder* and optionally its subfolders.

    Returns a tuple containing the number of moved and skipped files.
    """
    if not os.path.exists(folder):
        print(f"Error: Folder '{folder}' does not exist!")
        return 0, 0

    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory!")
        return 0, 0

    files_moved = 0
    files_skipped = 0

    for item in sorted(os.listdir(folder)):
        item_path = os.path.join(folder, item)

        if os.path.isdir(item_path):
            if recursive and item not in GENERATED_FOLDERS:
                print(f"\n📁 Organizing subfolder: {item}")
                moved, skipped = organize(item_path, recursive=True, dry_run=dry_run)
                files_moved += moved
                files_skipped += skipped
            continue

        if not os.path.isfile(item_path):
            files_skipped += 1
            continue

        category = _detect_category(item)
        if category == "Others" and not os.path.splitext(item)[1]:
            files_skipped += 1
            continue

        destination_folder = os.path.join(folder, category)
        if not dry_run:
            os.makedirs(destination_folder, exist_ok=True)

        destination = _unique_destination(os.path.join(destination_folder, item))

        if dry_run:
            print(f"[DRY RUN] {item} -> {category}/")
        else:
            shutil.move(item_path, destination)
            print(f"✓ {item} -> {category}/")

        files_moved += 1

    print(f"\n{'=' * 50}")
    print("📊 Organization Complete!")
    print(f"Files moved: {files_moved}")
    print(f"Files skipped: {files_skipped}")
    print(f"{'=' * 50}")

    return files_moved, files_skipped


def _prompt_for_input():
    """Prompt the user for a folder path and recursion preference."""
    folder = input("Enter folder path: ").strip()
    recursive_input = input("Organize subfolders recursively? (y/n): ").strip().lower()
    dry_run_input = input("Preview only without moving files? (y/n): ").strip().lower()
    return folder, recursive_input == "y", dry_run_input == "y"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files into folders by type.")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to organize")
    parser.add_argument("--recursive", "-r", action="store_true", help="Organize nested folders too")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview moves without changing files")
    args = parser.parse_args()

    if args.folder == "." and not any(os.sys.argv[1:]):
        folder, recursive_flag, dry_run_flag = _prompt_for_input()
    else:
        folder = args.folder
        recursive_flag = args.recursive
        dry_run_flag = args.dry_run

    organize(folder, recursive=recursive_flag, dry_run=dry_run_flag)
