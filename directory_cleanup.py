import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Base path for the user directories
base_path = "//dir/dir"

# Keywords to search for in the directories
keywords = ["Desktop", "Documents", "Autodesk", "Outlook", "Default", "Downloads", "Pictures"]

# Limit the number of user directories to explore
max_directories = 100

def get_drive_type():
    """Prompt the user for the type of drive and return the optimal number of workers."""
    drive_type = input("Are you deleting folders on an HDD or an SSD? [HDD/SSD]: ").strip().upper()
    if drive_type == "SSD":
        return 10  # Higher parallelism for SSDs
    elif drive_type == "HDD":
        return 4   # Lower parallelism for HDDs to avoid performance degradation
    else:
        print("Invalid input. Defaulting to SSD configuration.")
        return 10

def get_creation_time(directory):
    """Get the creation time of a directory."""
    return os.path.getctime(directory)

def delete_folder(folder_path):
    """Attempt to delete a folder and handle exceptions."""
    try:
        shutil.rmtree(folder_path)
        # ANSI escape code for red text
        print(f"\033[91mDeleted: {folder_path}\033[0m")
    except FileNotFoundError:
        print(f"File not found, skipping: {folder_path}")
    except Exception as e:
        print(f"Error deleting {folder_path}: {e}")

def process_keyword_folders(directory, keyword_folders, max_workers):
    """Filter and delete folders based on criteria, using multithreading."""
    print(f"Processing: {directory}")
    newest_folders = {}
    for keyword in keywords:
        filtered_folders = {name: time for name, time in keyword_folders.items() if keyword in name}
        if filtered_folders:
            newest = max(filtered_folders, key=filtered_folders.get)
            newest_folders[newest] = filtered_folders[newest]

    folders_to_delete = [os.path.join(directory, name) for name, time in keyword_folders.items() if name not in newest_folders]

    # Use ThreadPoolExecutor to parallelize folder deletion
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(delete_folder, folders_to_delete)

def search_directory(directory, max_workers):
    """Search the directory for folders matching keywords, optimized with os.scandir()."""
    print(f"Scanning: {directory}")
    keyword_folders = {}
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_dir() and any(keyword in entry.name for keyword in keywords):
                    keyword_folders[entry.name] = get_creation_time(entry.path)
    except PermissionError:
        print(f"Permission denied: {directory}")
    except FileNotFoundError:
        print(f"Directory not found: {directory}")
    # Process directories that contain more than one keyword folder
    if len(keyword_folders) > 1:
        process_keyword_folders(directory, keyword_folders, max_workers)

def main():
    max_workers = get_drive_type()
    user_directories = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))][:max_directories]
    
    # Use ThreadPoolExecutor to parallelize directory searches
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(lambda d: search_directory(d, max_workers), user_directories)

if __name__ == "__main__":
    main()
