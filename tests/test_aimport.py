import sys
import os
import pytest
import tempfile
import shutil
from unittest.mock import patch
from pathlib import Path

# Import required for project root path access
from aimport import *

# Import the module under test
from aimport import (
    _resolve_directory_path,
    _find_anchor_files_in_tree,
    _update_sys_path_unique,
    add_path_to_sys_path,
)


class TestResolveDirectoryPath:
    """Tests for _resolve_directory_path function."""

    def test_resolve_directory_path_with_file(self, tmp_path):
        """Test that file path is converted to directory path."""
        test_file = tmp_path / "test_file.py"
        test_file.touch()

        result = _resolve_directory_path(str(test_file))
        assert result == str(tmp_path)

    def test_resolve_directory_path_with_directory(self, tmp_path):
        """Test that directory path remains unchanged."""
        result = _resolve_directory_path(str(tmp_path))
        assert result == str(tmp_path)

    def test_resolve_directory_path_with_nonexistent_path(self):
        """Test with non-existent path (should treat as directory)."""
        nonexistent_path = "/some/nonexistent/path"
        result = _resolve_directory_path(nonexistent_path)
        assert result == nonexistent_path


class TestFindAnchorFilesInTree:
    """Tests for _find_anchor_files_in_tree function."""

    def test_find_anchor_files_single_level(self, tmp_path):
        """Test finding anchor file in single directory."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.touch()

        result = _find_anchor_files_in_tree(str(tmp_path), "__aimport__")
        assert result == [str(tmp_path)]

    def test_find_anchor_files_multiple_levels(self, tmp_path):
        """Test finding anchor files in multiple directory levels."""
        # Create nested directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create anchor files at different levels
        (tmp_path / "__aimport__").touch()
        (level2 / "__aimport__").touch()

        result = _find_anchor_files_in_tree(str(level3), "__aimport__")
        expected = [str(level2), str(tmp_path)]
        assert result == expected

    def test_find_anchor_files_no_files_found(self, tmp_path):
        """Test when no anchor files are found."""
        level1 = tmp_path / "level1"
        level1.mkdir()

        result = _find_anchor_files_in_tree(str(level1), "__aimport__")
        assert result == []

    def test_find_anchor_files_different_filename(self, tmp_path):
        """Test with different anchor filename."""
        init_file = tmp_path / "__init__.py"
        init_file.touch()

        result = _find_anchor_files_in_tree(str(tmp_path), "__init__.py")
        assert result == [str(tmp_path)]

    def test_find_anchor_files_filesystem_root(self, tmp_path):
        """Test traversal stops at filesystem root."""
        deep_path = tmp_path / "very" / "deep" / "path"
        deep_path.mkdir(parents=True)

        result = _find_anchor_files_in_tree(str(deep_path), "__nonexistent__")
        assert result == []


class TestUpdateSysPathUnique:
    """Tests for _update_sys_path_unique function."""

    def setUp(self):
        """Store original sys.path for restoration."""
        self.original_sys_path = sys.path[:]

    def tearDown(self):
        """Restore original sys.path."""
        sys.path[:] = self.original_sys_path

    def test_update_sys_path_unique_no_duplicates(self):
        """Test adding new paths without duplicates."""
        original_path = sys.path[:]
        new_paths = ["/new/path1", "/new/path2"]

        _update_sys_path_unique(new_paths)

        expected = new_paths + original_path
        assert sys.path == expected

        # Restore original
        sys.path[:] = original_path

    def test_update_sys_path_unique_with_duplicates(self):
        """Test that duplicates are removed."""
        original_path = ["/existing/path", "/another/path"]
        sys.path[:] = original_path
        new_paths = ["/new/path", "/existing/path", "/another/new/path"]

        _update_sys_path_unique(new_paths)

        expected = ["/new/path", "/existing/path", "/another/new/path", "/another/path"]
        assert sys.path == expected

        # Restore original
        sys.path[:] = original_path

    def test_update_sys_path_unique_empty_new_paths(self):
        """Test with empty new paths list."""
        original_path = sys.path[:]

        _update_sys_path_unique([])

        assert sys.path == original_path


class TestAddPathToSysPath:
    """Tests for add_path_to_sys_path function."""

    def setUp(self):
        """Store original sys.path for restoration."""
        self.original_sys_path = sys.path[:]

    def tearDown(self):
        """Restore original sys.path."""
        sys.path[:] = self.original_sys_path

    def test_add_path_to_sys_path_with_aimport_files(self, tmp_path):
        """Test path addition when __aimport__ files are found."""
        # Create directory structure with __aimport__ files
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        (tmp_path / "__aimport__").touch()
        (level1 / "__aimport__").touch()

        with patch("sys.path", [str(level2)]):
            add_path_to_sys_path(str(level2))

            # Should find __aimport__ files and add those paths
            assert str(level1) in sys.path
            assert str(tmp_path) in sys.path
            assert str(level2) in sys.path

    def test_add_path_to_sys_path_fallback_to_init(self, tmp_path):
        """Test fallback to __init__.py files when no __aimport__ files found."""
        # Create directory structure with __init__.py files only
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        (tmp_path / "__init__.py").touch()
        (level1 / "__init__.py").touch()

        with patch("sys.path", [str(level2)]):
            add_path_to_sys_path(str(level2))

            # Should find __init__.py files and add those paths
            assert str(level1) in sys.path
            assert str(tmp_path) in sys.path
            assert str(level2) in sys.path

    def test_add_path_to_sys_path_with_secondary_path(self, tmp_path):
        """Test with secondary path parameter."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "__aimport__").touch()

        with patch("sys.path", [str(tmp_path)]):
            add_path_to_sys_path(str(tmp_path), "subdir")

            assert str(subdir) in sys.path

    def test_add_path_to_sys_path_with_file_primary_path(self, tmp_path):
        """Test with file as primary path (should resolve to directory)."""
        test_file = tmp_path / "test.py"
        test_file.touch()
        (tmp_path / "__aimport__").touch()

        with patch("sys.path", [str(test_file)]):
            add_path_to_sys_path(str(test_file))

            assert str(tmp_path) in sys.path

    def test_add_path_to_sys_path_no_anchor_files(self, tmp_path):
        """Test when no anchor files are found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("sys.path", [str(empty_dir)]):
            add_path_to_sys_path(str(empty_dir))

            # Should still add the base path
            assert str(empty_dir) in sys.path

    def test_add_path_to_sys_path_default_parameters(self):
        """Test with default parameters (uses sys.path[0])."""
        original_path = sys.path[:]

        # This will use sys.path[0] as primary_path
        add_path_to_sys_path()

        # Should have modified sys.path
        assert len(sys.path) >= len(original_path)

        # Restore original
        sys.path[:] = original_path


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complex_directory_structure(self, tmp_path):
        """Test with complex directory structure mixing __aimport__ and __init__.py files."""
        # Create complex structure
        project_root = tmp_path / "project"
        src = project_root / "src"
        package = src / "mypackage"
        subpackage = package / "subpackage"
        subpackage.mkdir(parents=True)

        # Mix of __aimport__ and __init__.py files
        (project_root / "__aimport__").touch()
        (
            src / "__init__.py"
        ).touch()  # This should be ignored due to __aimport__ at root
        (package / "__aimport__").touch()
        (
            subpackage / "__init__.py"
        ).touch()  # This should be ignored due to __aimport__ files

        with patch("sys.path", [str(subpackage)]):
            add_path_to_sys_path(str(subpackage))

            # Should find __aimport__ files only
            assert str(package) in sys.path
            assert str(project_root) in sys.path
            assert str(subpackage) in sys.path
            # Should NOT include src (has __init__.py but __aimport__ takes precedence)

    def test_sys_path_ordering_preserved(self, tmp_path):
        """Test that sys.path ordering is preserved correctly."""
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        (tmp_path / "__aimport__").touch()
        (level1 / "__aimport__").touch()
        (level2 / "__aimport__").touch()

        original_sys_path = ["/original/path1", "/original/path2"]

        with patch("sys.path", original_sys_path):
            add_path_to_sys_path(str(level3))

            # New paths should be added first, then original paths
            assert sys.path.index(str(level3)) < sys.path.index("/original/path1")
            assert sys.path.index(str(level2)) < sys.path.index("/original/path1")
            assert sys.path.index(str(level1)) < sys.path.index("/original/path1")
            assert sys.path.index(str(tmp_path)) < sys.path.index("/original/path1")


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_string_paths(self):
        """Test behavior with empty string paths."""
        result = _find_anchor_files_in_tree("", "__aimport__")
        # Empty string path should return empty string as a path
        assert result == [""]

    def test_none_paths(self):
        """Test behavior with None paths."""
        with pytest.raises((TypeError, AttributeError)):
            _find_anchor_files_in_tree(None, "__aimport__")

    def test_very_deep_directory_structure(self, tmp_path):
        """Test with very deep directory structure."""
        # Create deep structure
        current = tmp_path
        for i in range(20):  # 20 levels deep
            current = current / f"level{i}"
        current.mkdir(parents=True)

        # Add anchor file at root
        (tmp_path / "__aimport__").touch()

        result = _find_anchor_files_in_tree(str(current), "__aimport__")
        assert str(tmp_path) in result

    def test_symlink_handling(self, tmp_path):
        """Test behavior with symbolic links."""
        if os.name == "nt":  # Skip on Windows due to symlink permissions
            pytest.skip("Skipping symlink test on Windows")

        # Create a real directory with __aimport__
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "__aimport__").touch()

        # Create a symlink to it
        link_dir = tmp_path / "link"
        os.symlink(real_dir, link_dir)

        result = _find_anchor_files_in_tree(str(link_dir), "__aimport__")
        # Should find the anchor file through the symlink
        assert len(result) >= 1
