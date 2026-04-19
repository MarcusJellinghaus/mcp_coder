"""Shared utility for finding executables on the system PATH."""

import platform
import shutil


def find_executable(name: str, *, install_hint: str) -> str:
    """Find executable by name via shutil.which().

    Args:
        name: Executable name (e.g. "copilot", "claude")
        install_hint: User-facing install instruction shown on failure

    Returns:
        Absolute path to the found executable.

    Raises:
        FileNotFoundError: If executable not found in PATH, with install_hint in message.
    """
    path = shutil.which(name)
    if path is None and platform.system() == "Windows":
        path = shutil.which(name + ".exe")
    if path is not None:
        return path
    raise FileNotFoundError(f"Executable '{name}' not found in PATH. {install_hint}")
