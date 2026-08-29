import os
import shutil

def organize(folder):
    files = {
        "Images": [".jpg", ".jpeg", ".png", ".gif"],
        "Videos": [".mp4", ".mkv", ".avi"],
        "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
        "Code": [".py", ".js", ".html", ".css"],
        "Archives": [".zip", ".rar", ".7z"]
    }

    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)

        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(file)[1].lower()
        matched = False
        
        for name, extensions in files.items():
            if ext in extensions:
                new_folder = os.path.join(folder, name)

                if not os.path.exists(new_folder):
                    os.mkdir(new_folder)

                shutil.move(file_path, os.path.join(new_folder, file))
                print(file, "->", name)
                matched = True
                break
                
                if not matched and ext:
                    others_folder = os.path.join(folder, "Others")
                  if not os.path.exists(others_folder):
                os.mkdir(others_folder)
            shutil.move(file_path, os.path.join(others_folder, file))
            print(file, "-> Others")

folder = input("Folder: ")
organize(folder)
print("Done")
