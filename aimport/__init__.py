import sys
import os
import pathlib


"""
Guido views running scripts within a package as an anti-pattern:
    rejected PEP-3122: https://www.python.org/dev/peps/pep-3122/#id1

I disagree. This is an ugly workaround.
"""


def _resolve_directory_path(path):
    """Convert file path to directory path if needed."""
    if os.path.isfile(path):
        return os.path.dirname(path)
    return path


def _find_anchor_files_in_tree(start_path, anchor_filename):
    """
    Traverse directory tree upward to find directories containing the specified anchor file.

    Args:
        start_path: Starting directory path
        anchor_filename: Name of the anchor file to search for

    Returns:
        List of directory paths containing the anchor file, in order found
    """
    found_paths = []
    current_path = start_path

    while True:
        anchor_file_path = os.path.join(current_path, anchor_filename)
        if pathlib.Path(anchor_file_path).exists():
            found_paths.append(current_path)

        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:  # Reached filesystem root
            break
        current_path = parent_path

    return found_paths


def _update_sys_path_unique(new_paths):
    """Update sys.path with new paths while avoiding duplicates."""
    combined_paths = new_paths + sys.path
    sys.path = []
    for path in combined_paths:
        if path not in sys.path:
            sys.path.append(path)


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
        base_path = os.path.join(base_path, secondary_path)

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
