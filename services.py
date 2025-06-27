import os
import re
import datetime


def log(msg):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")
    
def clear_annexes_names():
    existing_annexes = set()
    folder_path = "Annexes"
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        # Skip directories
        if not os.path.isfile(full_path):
            continue

        # Split name and extension
        name, ext = os.path.splitext(filename)

        # Clean the filename
        cleaned_name = re.sub(r'\s+', ' ', name.strip())

        # Skipt sent annexes
        if cleaned_name.endswith("_sent"):
            continue

        # Construct the new filename
        new_filename = f"{cleaned_name}{ext}"
        new_full_path = os.path.join(folder_path, new_filename)

        if not cleaned_name == "trmemail":
            existing_annexes.add(cleaned_name)

        # Only rename if the name has changed
        if filename != new_filename:
            print(f"Renaming: {filename} -> {new_filename}")
            os.rename(full_path, new_full_path)
    
    return existing_annexes


def check_annexes_folders():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "Annexes")

    entries = os.listdir(path)
    if not entries:
        return 'empty'

    folders = []
    files = []

    for name in entries:
        full_path = os.path.join(path, name)
        if os.path.isdir(full_path):
            folders.append(name)
        elif os.path.isfile(full_path):
            files.append(name)

    if folders and not files:
        return folders
    elif files and not folders:
        return 'only_files'
    else:
        return 'mixed'