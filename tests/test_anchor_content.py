import sys
import pytest
from pathlib import Path
from unittest.mock import patch

from aimport import (
    _read_anchor_file_content,
    _resolve_anchor_path,
    _find_anchor_files_in_tree,
    add_path_to_sys_path,
)


class TestReadAnchorFileContent:
    """Tests for _read_anchor_file_content function."""

    def test_read_anchor_file_with_content(self, tmp_path):
        """Test reading anchor file with valid content."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("  /some/path  \n")

        result = _read_anchor_file_content(anchor_file)
        assert result == ["/some/path"]

    def test_read_anchor_file_empty(self, tmp_path):
        """Test reading empty anchor file."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("")

        result = _read_anchor_file_content(anchor_file)
        assert result == []

    def test_read_anchor_file_whitespace_only(self, tmp_path):
        """Test reading anchor file with only whitespace."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("   \n\t  ")

        result = _read_anchor_file_content(anchor_file)
        assert result == []

    def test_read_anchor_file_nonexistent(self, tmp_path):
        """Test reading non-existent anchor file."""
        anchor_file = tmp_path / "__aimport__"

        result = _read_anchor_file_content(anchor_file)
        assert result == []

    def test_read_anchor_file_directory(self, tmp_path):
        """Test reading anchor file that is actually a directory."""
        anchor_dir = tmp_path / "__aimport__"
        anchor_dir.mkdir()

        result = _read_anchor_file_content(anchor_dir)
        assert result == []

    def test_read_anchor_file_unicode_error(self, tmp_path):
        """Test reading anchor file with invalid unicode."""
        anchor_file = tmp_path / "__aimport__"
        # Write binary data that will cause UnicodeDecodeError
        anchor_file.write_bytes(b"\xff\xfe\x00\x00")

        result = _read_anchor_file_content(anchor_file)
        assert result == []

    def test_read_anchor_file_multiple_paths(self, tmp_path):
        """Test reading anchor file with multiple paths."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("/path/one\n/path/two\n/path/three")

        result = _read_anchor_file_content(anchor_file)
        assert result == ["/path/one", "/path/two", "/path/three"]

    def test_read_anchor_file_multiple_paths_with_empty_lines(self, tmp_path):
        """Test reading anchor file with multiple paths and empty lines."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("/path/one\n\n/path/two\n   \n/path/three\n")

        result = _read_anchor_file_content(anchor_file)
        assert result == ["/path/one", "/path/two", "/path/three"]

    def test_read_anchor_file_single_path_multiline_format(self, tmp_path):
        """Test reading anchor file with single path in multiline format."""
        anchor_file = tmp_path / "__aimport__"
        anchor_file.write_text("  /single/path  \n")

        result = _read_anchor_file_content(anchor_file)
        assert result == ["/single/path"]


class TestResolveAnchorPath:
    """Tests for _resolve_anchor_path function."""

    def test_resolve_absolute_path(self, tmp_path):
        """Test resolving absolute path."""
        content = str(tmp_path / "some" / "path")
        anchor_dir = tmp_path / "anchor"

        result = _resolve_anchor_path(content, anchor_dir)
        assert result == Path(content).resolve()

    def test_resolve_relative_path(self, tmp_path):
        """Test resolving relative path."""
        anchor_dir = tmp_path / "anchor"
        anchor_dir.mkdir()
        content = "relative/path"

        result = _resolve_anchor_path(content, anchor_dir)
        expected = (anchor_dir / content).resolve()
        assert result == expected

    def test_resolve_empty_content(self, tmp_path):
        """Test resolving empty content."""
        result = _resolve_anchor_path("", tmp_path)
        assert result is None

    def test_resolve_none_content(self, tmp_path):
        """Test resolving None content."""
        result = _resolve_anchor_path(None, tmp_path)
        assert result is None

    def test_resolve_dot_path(self, tmp_path):
        """Test resolving current directory path."""
        anchor_dir = tmp_path / "anchor"
        anchor_dir.mkdir()
        content = "."

        result = _resolve_anchor_path(content, anchor_dir)
        assert result == anchor_dir.resolve()

    def test_resolve_parent_path(self, tmp_path):
        """Test resolving parent directory path."""
        anchor_dir = tmp_path / "anchor"
        anchor_dir.mkdir()
        content = ".."

        result = _resolve_anchor_path(content, anchor_dir)
        assert result == tmp_path.resolve()


class TestFindAnchorFilesWithContent:
    """Tests for _find_anchor_files_in_tree with content reading."""

    def test_find_anchor_files_with_multiple_absolute_paths(self, tmp_path):
        """Test finding anchor files with multiple absolute paths in content."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        # Create target directories
        target1 = tmp_path / "target1"
        target2 = tmp_path / "target2"
        target3 = tmp_path / "target3"
        target1.mkdir()
        target2.mkdir()
        target3.mkdir()

        # Create anchor file with multiple absolute paths
        (level1 / "__aimport__").write_text(f"{target1}\n{target2}\n{target3}")

        result = _find_anchor_files_in_tree(str(level2), "__aimport__")
        assert str(target1) in result
        assert str(target2) in result
        assert str(target3) in result

    def test_find_anchor_files_with_multiple_relative_paths(self, tmp_path):
        """Test finding anchor files with multiple relative paths in content."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        # Create target directories
        target1 = level1 / "rel_target1"
        target2 = level1 / "rel_target2"
        target1.mkdir()
        target2.mkdir()

        # Create anchor file with multiple relative paths
        (level1 / "__aimport__").write_text("rel_target1\nrel_target2")

        result = _find_anchor_files_in_tree(str(level2), "__aimport__")
        assert str(target1.resolve()) in result
        assert str(target2.resolve()) in result

    def test_find_anchor_files_mixed_valid_invalid_paths(self, tmp_path):
        """Test anchor file with mix of valid and invalid paths."""
        level1 = tmp_path / "level1"
        level1.mkdir()

        # Create one valid target
        target = level1 / "valid_target"
        target.mkdir()

        # Create anchor file with mix of valid/invalid paths
        (level1 / "__aimport__").write_text(f"valid_target\n/nonexistent/path\nrelative_target")

        result = _find_anchor_files_in_tree(str(level1), "__aimport__")
        # Should contain the valid target
        assert str(target.resolve()) in result
        # Should fall back to anchor file location for invalid paths
        assert str(level1) in result

    def test_find_anchor_files_multiple_files_multiple_paths(self, tmp_path):
        """Test multiple anchor files each with multiple paths."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create target directories
        target1 = tmp_path / "target1"
        target2 = tmp_path / "target2"
        target3 = tmp_path / "target3"  # Changed: create relative to tmp_path
        target4 = tmp_path / "target4"  # Changed: create relative to tmp_path
        target1.mkdir()
        target2.mkdir()
        target3.mkdir()
        target4.mkdir()

        # Create anchor files with multiple paths each
        (level2 / "__aimport__").write_text(f"{target1}\n{target2}")
        (tmp_path / "__aimport__").write_text("target3\ntarget4")

        result = _find_anchor_files_in_tree(str(level3), "__aimport__")
        assert str(target1) in result
        assert str(target2) in result
        # Note: target3 and target4 are resolved relative to tmp_path
        assert str((tmp_path / "target3").resolve()) in result
        assert str((tmp_path / "target4").resolve()) in result

    def test_find_anchor_files_with_relative_paths(self, tmp_path):
        """Test finding anchor files with relative paths in content."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        # Create target directories
        target1 = level1 / "relative_target"
        target2 = tmp_path / "another_target"
        target1.mkdir()
        target2.mkdir()

        # Create anchor files with relative paths
        (level1 / "__aimport__").write_text("relative_target")
        (tmp_path / "__aimport__").write_text("another_target")

        result = _find_anchor_files_in_tree(str(level2), "__aimport__")
        assert str(target1.resolve()) in result
        assert str(target2.resolve()) in result

    def test_find_anchor_files_empty_content_fallback(self, tmp_path):
        """Test fallback to file location when content is empty."""
        level1 = tmp_path / "level1"
        level1.mkdir()

        # Create empty anchor file
        (level1 / "__aimport__").write_text("")

        result = _find_anchor_files_in_tree(str(level1), "__aimport__")
        assert str(level1) in result

    def test_find_anchor_files_invalid_path_fallback(self, tmp_path):
        """Test fallback to file location when path doesn't exist."""
        level1 = tmp_path / "level1"
        level1.mkdir()

        # Create anchor file with non-existent path
        (level1 / "__aimport__").write_text("/nonexistent/path")

        result = _find_anchor_files_in_tree(str(level1), "__aimport__")
        assert str(level1) in result

    def test_find_anchor_files_mixed_content_and_empty(self, tmp_path):
        """Test mix of files with content and empty files."""
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level2.mkdir(parents=True)

        # Create target directory
        target = tmp_path / "target"
        target.mkdir()

        # One file with content, one empty
        (level1 / "__aimport__").write_text(str(target))
        (tmp_path / "__aimport__").write_text("")

        result = _find_anchor_files_in_tree(str(level2), "__aimport__")
        assert str(target) in result
        assert str(tmp_path) in result

    def test_find_anchor_files_with_init_py_content(self, tmp_path):
        """Test finding __init__.py files with content."""
        level1 = tmp_path / "level1"
        level1.mkdir()

        # Create target directory
        target = tmp_path / "target"
        target.mkdir()

        # Create __init__.py with content (no __aimport__ files)
        (level1 / "__init__.py").write_text(str(target))

        result = _find_anchor_files_in_tree(str(level1), "__init__.py")
        assert str(target) in result


class TestAddPathToSysPathWithContent:
    """Integration tests for add_path_to_sys_path with content reading."""

    def setUp(self):
        """Store original sys.path for restoration."""
        self.original_sys_path = sys.path[:]

    def tearDown(self):
        """Restore original sys.path."""
        sys.path[:] = self.original_sys_path

    def test_add_path_with_multiple_anchor_paths_absolute(self, tmp_path):
        """Test adding multiple paths from anchor file with absolute paths."""
        # Create directories
        start_dir = tmp_path / "start"
        target1 = tmp_path / "target1"
        target2 = tmp_path / "target2"
        target3 = tmp_path / "target3"
        start_dir.mkdir()
        target1.mkdir()
        target2.mkdir()
        target3.mkdir()

        # Create anchor file with multiple absolute paths
        (start_dir / "__aimport__").write_text(f"{target1}\n{target2}\n{target3}")

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            assert str(target1) in sys.path
            assert str(target2) in sys.path
            assert str(target3) in sys.path
            assert str(start_dir) in sys.path

    def test_add_path_with_multiple_anchor_paths_relative(self, tmp_path):
        """Test adding multiple paths from anchor file with relative paths."""
        # Create directories
        start_dir = tmp_path / "start"
        target1 = start_dir / "rel1"
        target2 = start_dir / "rel2"
        start_dir.mkdir()
        target1.mkdir()
        target2.mkdir()

        # Create anchor file with multiple relative paths
        (start_dir / "__aimport__").write_text("rel1\nrel2")

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            assert str(target1.resolve()) in sys.path
            assert str(target2.resolve()) in sys.path
            assert str(start_dir) in sys.path

    def test_add_path_multiple_files_multiple_paths_each(self, tmp_path):
        """Test with multiple anchor files each containing multiple paths."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create target directories
        target1 = tmp_path / "target1"
        target2 = tmp_path / "target2"
        target3 = level1 / "target3"
        target4 = level1 / "target4"
        target1.mkdir()
        target2.mkdir()
        target3.mkdir()
        target4.mkdir()

        # Create anchor files with multiple paths each
        (level2 / "__aimport__").write_text(f"{target1}\n{target2}")
        (level1 / "__aimport__").write_text("target3\ntarget4")

        with patch("sys.path", [str(level3)]):
            add_path_to_sys_path(str(level3))

            assert str(target1) in sys.path
            assert str(target2) in sys.path
            assert str((level1 / "target3").resolve()) in sys.path
            assert str((level1 / "target4").resolve()) in sys.path
            assert str(level3) in sys.path

    def test_add_path_mixed_valid_invalid_multiple_paths(self, tmp_path):
        """Test with anchor file containing mix of valid and invalid paths."""
        start_dir = tmp_path / "start"
        valid_target = start_dir / "valid"
        start_dir.mkdir()
        valid_target.mkdir()

        # Create anchor file with mix of valid/invalid paths
        (start_dir / "__aimport__").write_text("valid\n/nonexistent/path1\n/nonexistent/path2")

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            assert str(valid_target.resolve()) in sys.path
            # Should fall back to anchor file location for invalid paths
            assert str(start_dir) in sys.path

    def test_add_path_with_anchor_content_relative(self, tmp_path):
        """Test adding paths from anchor file with relative path content."""
        # Create directories
        start_dir = tmp_path / "start"
        target_dir = start_dir / "target"
        start_dir.mkdir()
        target_dir.mkdir()

        # Create anchor file with relative path
        (start_dir / "__aimport__").write_text("target")

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            assert str(target_dir.resolve()) in sys.path
            assert str(start_dir) in sys.path

    def test_add_path_mixed_content_and_location_anchors(self, tmp_path):
        """Test with mix of anchor files with content and without."""
        # Create directory structure
        level1 = tmp_path / "level1"
        level2 = level1 / "level2"
        level3 = level2 / "level3"
        level3.mkdir(parents=True)

        # Create target directories
        target1 = tmp_path / "target1"
        target2 = tmp_path / "target2"
        target1.mkdir()
        target2.mkdir()

        # Create anchor files: one with content, one empty
        (level2 / "__aimport__").write_text(str(target1))
        (tmp_path / "__aimport__").write_text("")  # Empty

        with patch("sys.path", [str(level3)]):
            add_path_to_sys_path(str(level3))

            assert str(target1) in sys.path  # From content
            assert str(tmp_path) in sys.path  # From file location
            assert str(level3) in sys.path

    def test_add_path_fallback_to_init_with_content(self, tmp_path):
        """Test fallback to __init__.py files when no __aimport__ files exist."""
        # Create directory structure
        start_dir = tmp_path / "start"
        target_dir = tmp_path / "target"
        start_dir.mkdir()
        target_dir.mkdir()

        # Create __init__.py with content (no __aimport__ files)
        (start_dir / "__init__.py").write_text(str(target_dir))

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            assert str(target_dir) in sys.path
            assert str(start_dir) in sys.path

    def test_add_path_nonexistent_target_fallback(self, tmp_path):
        """Test fallback when anchor content points to non-existent path."""
        start_dir = tmp_path / "start"
        start_dir.mkdir()

        # Create anchor file with non-existent path
        (start_dir / "__aimport__").write_text("/completely/nonexistent/path")

        with patch("sys.path", [str(start_dir)]):
            add_path_to_sys_path(str(start_dir))

            # Should fall back to anchor file location
            assert str(start_dir) in sys.path

    def test_add_path_complex_structure_with_content(self, tmp_path):
        """Test complex directory structure with mixed content types."""
        # Create complex structure
        project = tmp_path / "project"
        src = project / "src"
        lib = project / "lib"
        tests = project / "tests"
        deep = tests / "deep" / "nested"
        deep.mkdir(parents=True)
        src.mkdir()
        lib.mkdir()

        # Create target directories
        vendor = project / "vendor"
        external = tmp_path / "external"
        vendor.mkdir()
        external.mkdir()

        # Create anchor files with different content types
        (project / "__aimport__").write_text(str(external))  # Absolute
        (tests / "__aimport__").write_text("../vendor")  # Relative
        (deep / "__aimport__").write_text("")  # Empty

        with patch("sys.path", [str(deep)]):
            add_path_to_sys_path(str(deep))

            assert str(deep) in sys.path
            assert str(vendor.resolve()) in sys.path  # From relative path
            assert str(external) in sys.path  # From absolute path
