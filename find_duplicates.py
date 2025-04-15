import os
import hashlib
import re
from collections import defaultdict

def get_file_hash(filepath):
    """Get a hash of the file content."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_normalized_content(filepath):
    """Get normalized content (removing comments, whitespace)."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Remove comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)
    content = re.sub(r"'''.*?'''", '', content, flags=re.DOTALL)
    
    # Remove whitespace
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()

def find_duplicate_files(directory, extensions=None):
    """Find duplicate files in the directory."""
    if extensions is None:
        extensions = ['.py']
    
    # Maps hash to list of files with that hash
    hash_to_files = defaultdict(list)
    
    # Maps normalized content hash to list of files
    content_hash_to_files = defaultdict(list)
    
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, filename)
                
                # Skip symbolic links
                if os.path.islink(filepath):
                    continue
                
                try:
                    # Get file hash
                    file_hash = get_file_hash(filepath)
                    hash_to_files[file_hash].append(filepath)
                    
                    # Get normalized content hash
                    normalized_content = get_normalized_content(filepath)
                    content_hash = hashlib.md5(normalized_content.encode()).hexdigest()
                    content_hash_to_files[content_hash].append(filepath)
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    
    # Find duplicates
    exact_duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    similar_duplicates = {h: files for h, files in content_hash_to_files.items() 
                         if len(files) > 1 and h not in exact_duplicates}
    
    return exact_duplicates, similar_duplicates

if __name__ == "__main__":
    exact_duplicates, similar_duplicates = find_duplicate_files(".")
    
    print("=== Exact Duplicates ===")
    for hash_val, files in exact_duplicates.items():
        print(f"Hash: {hash_val}")
        for file in files:
            print(f"  {file}")
        print()
    
    print("=== Similar Duplicates (same content after normalization) ===")
    for hash_val, files in similar_duplicates.items():
        print(f"Hash: {hash_val}")
        for file in files:
            print(f"  {file}")
        print()
