import sys
from pathlib import Path


"""
Guido views running scripts within a package as an anti-pattern:
    rejected PEP-3122: https://www.python.org/dev/peps/pep-3122/#id1

I disagree. This is an ugly workaround.
"""


def _resolve_directory_path(path):
    """Convert file path to directory path if needed."""
    if not path:
        return path
    path_obj = Path(path)
    return str(path_obj.parent if path_obj.is_file() else path_obj)


def _read_anchor_file_content(anchor_file_path):
    """Read and return list of paths from anchor file if it exists and contains valid paths."""
    try:
        anchor_path = Path(anchor_file_path)
        if anchor_path.exists() and anchor_path.is_file():
            content = anchor_path.read_text().strip()
            if content:
                # Split by lines and filter out empty lines after stripping
                paths = [line.strip() for line in content.split('\n') if line.strip()]
                return paths
    except (OSError, UnicodeDecodeError):
        pass
    return []


def _resolve_anchor_path(content, anchor_file_dir):
    """Resolve anchor path content to absolute path."""
    if not content:
        return None

    content_path = Path(content)
    if content_path.is_absolute():
        return content_path.resolve()
    else:
        # Relative path - join with anchor file directory
        return (Path(anchor_file_dir) / content_path).resolve()


def _find_anchor_files_in_tree(start_path, anchor_filename):
    """
    Traverse directory tree upward to find directories containing the specified anchor file.
    If anchor files contain valid paths, use those paths instead of file locations.

    Args:
        start_path: Starting directory path
        anchor_filename: Name of the anchor file to search for

    Returns:
        List of directory paths (either anchor file locations or paths from their content), in order found
    """
    found_paths = []

    # Handle empty string case
    if start_path == "":
        current_path = Path(".")
        original_start_path = ""
    else:
        current_path = Path(start_path)
        original_start_path = start_path

    while True:
        anchor_file_path = current_path / anchor_filename
        if anchor_file_path.exists():
            # Check if anchor file contains valid paths
            anchor_paths = _read_anchor_file_content(anchor_file_path)
            if anchor_paths:
                # Process each path from file content
                any_valid_path = False
                any_invalid_path = False
                for anchor_content in anchor_paths:
                    resolved_path = _resolve_anchor_path(anchor_content, current_path)
                    if resolved_path and resolved_path.exists():
                        found_paths.append(str(resolved_path))
                        any_valid_path = True
                    else:
                        any_invalid_path = True
                
                # Add anchor file location as fallback if any invalid paths found
                if any_invalid_path:
                    if str(current_path) == "." and original_start_path == "":
                        found_paths.append("")
                    else:
                        found_paths.append(str(current_path))
            else:
                # Use anchor file location (empty file or no valid paths)
                if str(current_path) == "." and original_start_path == "":
                    found_paths.append("")
                else:
                    found_paths.append(str(current_path))

        parent_path = current_path.parent
        if parent_path == current_path:  # Reached filesystem root
            break
        current_path = parent_path

    return found_paths


def _update_sys_path_unique(new_paths):
    """Update sys.path with new paths while avoiding duplicates."""
    # Start with existing sys.path
    existing_paths = sys.path[:]
    sys.path.clear()

    # Add new paths first (using insert order)
    for path in new_paths:
        if path not in sys.path:
            sys.path.append(path)

    # Then add existing paths that aren't already present
    for path in existing_paths:
        if path not in sys.path:
            sys.path.append(path)

    # Remove duplicates: iterate from beginning, if duplicate found later, remove later one
    seen = set()
    unique_paths = []
    for path in sys.path:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    
    sys.path[:] = unique_paths


def add_path_to_sys_path(primary_path=sys.path[0], secondary_path=None):
    """
    Add paths to sys.path based on anchor files found in directory tree.

    Args:
        primary_path: Primary path to start search from (default: sys.path[0])
        secondary_path: Optional secondary path to join with primary_path
    """
    # Resolve the starting directory path
    base_path = _resolve_directory_path(primary_path)

    if secondary_path is not None:
        secondary_path = _resolve_directory_path(secondary_path)
        base_path = str(Path(base_path) / secondary_path)

    paths_to_add = [base_path]

    # First, search for __aimport__ files as anchors
    aimport_paths = _find_anchor_files_in_tree(base_path, "__aimport__")

    if aimport_paths:
        # __aimport__ files found - use these as anchors
        paths_to_add.extend(aimport_paths)
    else:
        # No __aimport__ files found - fall back to __init__.py files
        init_paths = _find_anchor_files_in_tree(base_path, "__init__.py")
        paths_to_add.extend(init_paths)

    # Update sys.path with found paths
    _update_sys_path_unique(paths_to_add)
    # print(f"sys.path: {sys.path}")


# Execute the path setup automatically when module is imported
add_path_to_sys_path()
