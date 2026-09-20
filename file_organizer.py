import os
import shutil


FILE_CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif"},
    "Videos": {".mp4", ".mkv", ".avi"},
    "Documents": {".pdf", ".docx", ".txt", ".xlsx"},
    "Code": {".py", ".js", ".html", ".css"},
    "Archives": {".zip", ".rar", ".7z"},
}


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


def organize(folder, recursive=False):
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
    generated_folders = set(FILE_CATEGORIES) | {"Others"}

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        if os.path.isdir(file_path):
            if recursive and file not in generated_folders:
                print(f"\n📁 Organizing subfolder: {file}")
                moved, skipped = organize(file_path, recursive=True)
                files_moved += moved
                files_skipped += skipped
            continue

        if not os.path.isfile(file_path):
            files_skipped += 1
            continue

        extension = os.path.splitext(file)[1].lower()
        if not extension:
            files_skipped += 1
            continue

        category = next(
            (name for name, extensions in FILE_CATEGORIES.items() if extension in extensions),
            "Others",
        )
        destination_folder = os.path.join(folder, category)
        os.makedirs(destination_folder, exist_ok=True)
        destination = _unique_destination(os.path.join(destination_folder, file))

        shutil.move(file_path, destination)
        print(f"✓ {file} -> {category}/")
        files_moved += 1

    print(f"\n{'=' * 50}")
    print("📊 Organization Complete!")
    print(f"Files moved: {files_moved}")
    print(f"Files skipped: {files_skipped}")
    print(f"{'=' * 50}")

    return files_moved, files_skipped


if __name__ == "__main__":
    folder = input("Enter folder path: ").strip()
    recursive_input = input("Organize subfolders recursively? (y/n): ").strip().lower()
    organize(folder, recursive=recursive_input == "y")
