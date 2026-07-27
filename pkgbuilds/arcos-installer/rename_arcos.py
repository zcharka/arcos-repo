import os

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content.replace("Linexin", "ArcOS").replace("linexin", "arcos")
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        pass # Ignore binary files or errors

def process_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            replace_in_file(filepath)

if __name__ == "__main__":
    src_dir = "/home/Sebastian/Documents/arcos-repo/pkgbuilds/arcos-installer/src"
    process_dir(src_dir)
    
    # Rename folder if it exists
    old_folder = os.path.join(src_dir, "usr/share/linexin-installer")
    new_folder = os.path.join(src_dir, "usr/share/arcos-installer")
    if os.path.exists(old_folder):
        os.rename(old_folder, new_folder)
        print("Renamed folder to arcos-installer")
