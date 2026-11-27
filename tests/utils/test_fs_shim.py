"""The fs shim re-exports exactly the shared line-ending and containment helpers."""

from mcp_coder.utils import fs


def test_fs_shim_exports_only_the_shared_helpers() -> None:
    # read_file / normalize_path are not re-exported: their names clash with
    # local functions of different meaning.
    assert sorted(fs.__all__) == ["check_path_within", "dominant_newline", "write_text"]
