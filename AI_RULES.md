# AI Rules for meteoros-floripa-bin

This document outlines the technical stack and recommended library usage for the `meteoros-floripa-bin` project.

## Tech Stack Overview

*   **Primary Language**: Python 3
*   **Database**: SQLite (using `sqlite3` module) for local data storage.
*   **Configuration Management**: YAML files (parsed with `PyYAML`) for application settings.
*   **Image Processing**: Pillow (PIL) for image manipulation, such as stacking multiple images.
*   **Version Control Integration**: GitPython for programmatic interaction with Git repositories (e.g., committing and pushing changes).
*   **File Operations (Windows Specific)**: `robocopy` (via a Python wrapper) for efficient file synchronization and uploads on Windows systems.
*   **Video Conversion**: `subprocess` module to execute external command-line tools (like `ffmpeg`) for video format conversion.
*   **Data Parsing**:
    *   CSV files are parsed using Python's built-in `csv` module.
    *   XML files are parsed using Python's built-in `xml.dom.minidom` module.
*   **Utility Functions**: Custom utility modules (`utils/captures.py`, `utils/config.py`, `utils/database.py`, `utils/utils.py`, `utils/video.py`) for specific application logic.

## Library Usage Guidelines

*   **Database**: Always use the `sqlite3` module for all database interactions. Do not introduce other ORMs or database connectors.
*   **Configuration**: Use `PyYAML` for loading and parsing `.yml` configuration files.
*   **Image Manipulation**: `Pillow` is the designated library for any image processing tasks.
*   **Git Operations**: Use `GitPython` for any automated Git commands (add, commit, push).
*   **File Copying**: For robust file copying on Windows, leverage the `robocopy` wrapper. For cross-platform file operations, use standard `os` and `shutil` modules.
*   **External Commands**: When interacting with external command-line tools (e.g., `ffmpeg`), use Python's `subprocess` module.
*   **Data Formats**:
    *   For CSV data, use the `csv` module.
    *   For XML data, use `xml.dom.minidom`.
    *   For JSON data, use the `json` module.