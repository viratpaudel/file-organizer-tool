import os
import shutil
from pathlib import Path

def organize(folder, recursive=False):
    if not os.path.exists(folder):
        print(f"Error: Folder '{folder}' does not exist!")
        return
    
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a directory!")
        return
    
    files = {
        "Images": [".jpg", ".jpeg", ".png", ".gif"],
        "Videos": [".mp4", ".mkv", ".avi"],
        "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
        "Code": [".py", ".js", ".html", ".css"],
        "Archives": [".zip", ".rar", ".7z"]
    }

files_moved = 0
    files_skipped = 0

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        if  os.path.isdir(file_path):
            if recursive:
                print(f"\n📁 Organizing subfolder: {file}")
                organize(file_path, recursive=True)
            continue
                    if not os.path.isfile(file_path)
                        continue
         
        ext = os.path.splitext(file)[1].lower()
        matched = False
        
        for name, extensions in files.items():
            if ext in extensions:
                new_folder = os.path.join(folder, name)

                if not os.path.exists(new_folder):
                    os.mkdir(new_folder)

                new_path = os.path.join(new_folder, file)
                
        
                if file_path != new_path:
                    shutil.move(file_path, new_path)
                    print(f"✓ {file} -> {name}/")
                    files_moved += 1
                    matched = True
                    break
        
        
        if not matched and ext:
            others_folder = os.path.join(folder, "Others")
            if not os.path.exists(others_folder):
                os.mkdir(others_folder)
            new_path = os.path.join(others_folder, file)
            
            
            if file_path != new_path:
                shutil.move(file_path, new_path)
                print(f"✓ {file} -> Others/")
                files_moved += 1
        elif not ext:
            
            files_skipped += 1

    
    print(f"\n{'='*50}")
    print(f"📊 Organization Complete!")
    print(f"Files moved: {files_moved}")
    print(f"Files skipped: {files_skipped}")
    print(f"{'='*50}")


folder = input("Enter folder path: ").strip()
recursive_input = input("Organize subfolders recursively? (y/n): ").strip().lower()
recursive = recursive_input == 'y'

organize(folder, recursive=recursive)
