import argparse
import fnmatch
import json
import os
import shutil


DEFAULT_FILE_CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".heif", ".tif", ".tiff"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx", ".md", ".rtf"},
    "Code": {".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".html", ".css", ".json", ".xml", ".sql", ".yaml", ".yml"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"},
    "Executables": {".exe", ".msi", ".dmg", ".apk"},
    "Spreadsheets": {".csv", ".ods"},
}


def _normalize_category_map(category_map):
    """Normalize a custom category map into ext -> category pairs."""
    if not category_map:
        return {}

    result = {}
    for item in category_map:
        if not isinstance(item, str):
            continue

        if "=" not in item:
            raise ValueError(f"Invalid category mapping '{item}'. Use EXT=CATEGORY format.")

        extension, category = item.split("=", 1)
        extension = extension.strip().lower()
        category = category.strip()

        if not extension or not category:
            raise ValueError(f"Invalid category mapping '{item}'.")

        if not extension.startswith("."):
            extension = "." + extension

        result[extension] = category

    return result


def _merge_categories(custom_map=None):
    """Return a complete category map with default categories plus custom mappings."""
    merged = {category: set(exts) for category, exts in DEFAULT_FILE_CATEGORIES.items()}

    if not custom_map:
        return merged

    for ext, category in custom_map.items():
        if category not in merged:
            merged[category] = set()
        merged[category].add(ext.lower())

    return merged


def _matches_pattern(name, patterns):
    """Check whether a name matches any ignore pattern."""
    if not patterns:
        return False

    normalized_name = name.lower()
    for pattern in patterns:
        if not pattern:
            continue

        normalized_pattern = pattern.lower()
        if normalized_pattern == "*":
            return True

        if fnmatch.fnmatchcase(normalized_name, normalized_pattern):
            return True

        if normalized_pattern in normalized_name or normalized_name.endswith(normalized_pattern):
            return True

    return False


def _is_ignored(path, name, ignore_patterns=None, ignore_dirs=None):
    """Return True if a file or folder should be skipped."""
    ignore_patterns = ignore_patterns or []
    ignore_dirs = ignore_dirs or []

    if _matches_pattern(name, ignore_patterns):
        return True

    normalized_name = os.path.basename(path).lower()
    for ignored_dir in ignore_dirs:
        if ignored_dir and ignored_dir.lower() in normalized_name:
            return True

    return False


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


def _detect_category(filename, categories):
    """Return the category name for a filename based on its extension."""
    extension = os.path.splitext(filename)[1].lower()
    if not extension:
        return "Others"

    for category, extensions in categories.items():
        if extension in extensions:
            return category

    return "Others"


def _log_event(message, log_file=None):
    """Write a message to the console and optionally to a log file."""
    print(message)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as log_handle:
            log_handle.write(message + "\n")


def _confirm_action(prompt_text):
    """Prompt for confirmation before moving a file."""
    response = input(f"{prompt_text} (y/n): ").strip().lower()
    return response in {"y", "yes"}


def organize(
    folder,
    recursive=False,
    dry_run=False,
    max_depth=None,
    category_map=None,
    log_file=None,
    ignore_patterns=None,
    ignore_dirs=None,
    ask_before_move=False,
    summary_file=None,
    current_depth=0,
):
    """Organize files in *folder* and optionally its subfolders.

    Returns a tuple containing the number of moved and skipped files.
    """
    categories = _merge_categories(category_map)
    generated_folders = set(categories) | {"Others"}

    if not os.path.exists(folder):
        _log_event(f"Error: Folder '{folder}' does not exist!", log_file)
        return 0, 0

    if not os.path.isdir(folder):
        _log_event(f"Error: '{folder}' is not a directory!", log_file)
        return 0, 0

    files_moved = 0
    files_skipped = 0
    moved_files = []
    skipped_files = []

    for item in sorted(os.listdir(folder)):
        item_path = os.path.join(folder, item)

        if _is_ignored(item_path, item, ignore_patterns, ignore_dirs):
            skipped_files.append(f"ignored: {item_path}")
            continue

        if os.path.isdir(item_path):
            if recursive and item not in generated_folders:
                if max_depth is not None and current_depth >= max_depth:
                    continue

                _log_event(f"\n📁 Organizing subfolder: {item}", log_file)
                moved, skipped = organize(
                    item_path,
                    recursive=True,
                    dry_run=dry_run,
                    max_depth=max_depth,
                    category_map=category_map,
                    log_file=log_file,
                    ignore_patterns=ignore_patterns,
                    ignore_dirs=ignore_dirs,
                    ask_before_move=ask_before_move,
                    summary_file=summary_file,
                    current_depth=current_depth + 1,
                )
                files_moved += moved
                files_skipped += skipped
                moved_files.extend([f"subfolder move: {item_path}"])
            continue

        if not os.path.isfile(item_path):
            files_skipped += 1
            skipped_files.append(f"not file: {item_path}")
            continue

        extension = os.path.splitext(item)[1].lower()
        category = _detect_category(item, categories)

        if not extension:
            files_skipped += 1
            skipped_files.append(f"no extension: {item_path}")
            continue

        if category == "Others":
            files_skipped += 1
            skipped_files.append(f"unknown type: {item_path}")
            continue

        target_folder = os.path.join(folder, category)
        if not dry_run:
            os.makedirs(target_folder, exist_ok=True)

        destination = _unique_destination(os.path.join(target_folder, item))

        if ask_before_move:
            proceed = _confirm_action(f"Move '{item}' to '{category}' folder?")
            if not proceed:
                skipped_files.append(f"declined: {item_path}")
                continue

        if dry_run:
            _log_event(f"[DRY RUN] {item} -> {category}/", log_file)
        else:
            if os.path.abspath(item_path) == os.path.abspath(destination):
                _log_event(f"Skipping '{item}' because it is already in the destination folder.", log_file)
                files_skipped += 1
                skipped_files.append(f"already organized: {item_path}")
                continue
            shutil.move(item_path, destination)
            _log_event(f"✓ {item} -> {category}/", log_file)
            moved_files.append(f"{item_path} -> {destination}")

        files_moved += 1

    _log_event(f"\n{'=' * 50}", log_file)
    _log_event("📊 Organization Complete!", log_file)
    _log_event(f"Files moved: {files_moved}", log_file)
    _log_event(f"Files skipped: {files_skipped}", log_file)
    _log_event(f"{'=' * 50}", log_file)

    if summary_file:
        summary = {
            "folder": os.path.abspath(folder),
            "files_moved": files_moved,
            "files_skipped": files_skipped,
            "moved_files": moved_files,
            "skipped_files": skipped_files,
        }
        with open(summary_file, "w", encoding="utf-8") as out_file:
            json.dump(summary, out_file, indent=2)

    return files_moved, files_skipped


def _prompt_for_input():
    """Prompt the user for a folder path and optional settings."""
    folder = input("Enter folder path: ").strip()
    recursive_input = input("Organize subfolders recursively? (y/n): ").strip().lower()
    dry_run_input = input("Preview only without moving files? (y/n): ").strip().lower()
    max_depth_input = input("Max subfolder depth (leave blank for unlimited): ").strip()
    custom_map_input = input("Custom mappings (optional, format: .ext=Category; .mp4=Videos): ").strip()
    ignore_input = input("Ignore names/patterns (optional, comma-separated): ").strip()
    ask_input = input("Ask before each move? (y/n): ").strip().lower()
    return (
        folder,
        recursive_input == "y",
        dry_run_input == "y",
        int(max_depth_input) if max_depth_input else None,
        custom_map_input,
        [part.strip() for part in ignore_input.split(",") if part.strip()],
        ask_input == "y",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files into folders by type.")
    parser.add_argument("folder", nargs="?", default=".", help="Folder to organize")
    parser.add_argument("--recursive", "-r", action="store_true", help="Organize nested folders too")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview moves without changing files")
    parser.add_argument("--max-depth", type=int, default=None, help="Limit recursive scans to a specific depth")
    parser.add_argument(
        "--category-map",
        nargs="*",
        default=[],
        help="Custom extension mappings in EXT=CATEGORY format, such as .svg=Images .csv=Documents",
    )
    parser.add_argument("--log-file", default=None, help="Write all actions to a log file")
    parser.add_argument("--ignore", nargs="*", default=[], help="Ignore files/folders matching these names or patterns")
    parser.add_argument("--ignore-dir", nargs="*", default=[], help="Do not traverse folders whose names match these values")
    parser.add_argument("--ask-before-move", action="store_true", help="Ask for confirmation before moving each file")
    parser.add_argument("--summary-json", default=None, help="Write a JSON summary report to the given file")
    args = parser.parse_args()

    if args.folder == "." and not any(os.sys.argv[1:]):
        (
            folder,
            recursive_flag,
            dry_run_flag,
            max_depth,
            custom_map_input,
            ignore_input,
            ask_before_move,
        ) = _prompt_for_input()
        custom_map = _normalize_category_map([part.strip() for part in custom_map_input.split(";") if part.strip()])
    else:
        folder = args.folder
        recursive_flag = args.recursive
        dry_run_flag = args.dry_run
        max_depth = args.max_depth
        custom_map = _normalize_category_map(args.category_map)
        ignore_input = args.ignore
        ask_before_move = args.ask_before_move

    organize(
        folder,
        recursive=recursive_flag,
        dry_run=dry_run_flag,
        max_depth=max_depth,
        category_map=custom_map,
        log_file=args.log_file,
        ignore_patterns=ignore_input,
        ignore_dirs=args.ignore_dir,
        ask_before_move=ask_before_move,
        summary_file=args.summary_json,
    )
