# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-01-27

### Added
- **Undo functionality** - revert last rename operation
  - CLI: `--undo`, `--history`, `--clear-history` commands
  - GUI: Edit menu with "Undo" (Ctrl+Z), "Show history", "Clear history"
- New module: `history_manager.py` for tracking rename operations
- Hidden `.rename_history.json` file stores up to 10 operations per folder
- Automatic cleanup of empty folders after undo

### Fixed
- CLI argument parsing bug (duplicate increment)
- Windows hidden file permission handling

## [1.3.0] - 2026-01-26

### Added
- **GUI support** for custom filename templates
- **GUI support** for folder organization (Year/Month)
- Settings panel in GUI for easier configuration
- Auto-creation of target directories during folder organization
- Improved duplicate handling when using custom templates

## [1.2.0] - 2026-01-25

### Added
- **Custom filename templates** - `--template` argument with 10 variables
  - Variables: `{type}`, `{YYYY}`, `{YY}`, `{MM}`, `{DD}`, `{HH}`, `{hh}`, `{mm}`, `{ss}`, `{HHmmss}`
  - Example: `--template "IMG_{YYYY}{MM}{DD}_{HHmmss}"`
- **Folder organization** - `--organize` argument with 4 modes
  - Modes: `none`, `year`, `year-month`, `date`
  - Example: `--organize year-month` creates `2023/08/` structure
- New modules: `template_parser.py`, `folder_organizer.py`
- Updated help with new options

### Changed
- Version updated to 1.2
- Improved CLI help text

## [1.1.0] - 2026-01-22

### Added
- **Detection of already renamed files** - Program now automatically detects files that match the `Photo/Video-YYYY-MM-DD_HHMMSS` pattern
- **Interactive dialog** for handling previously renamed files:
  - Skip (process only new files)
  - Re-rename (recalculate dates from metadata)
  - Cancel operation
- CLI version: ASCII-styled box with file examples
- GUI version: Modal dialog with scrollable file list
- Separate statistics for already renamed vs new files

### Changed
- Improved `process_file()` logic for correct handling of re-renaming
- Better user experience with clear action choices

## [1.0.0] - 2026-01-21

### Added
- Initial release
- **49 supported formats**: 26 photo formats + 23 video formats
- **Photo formats**: JPG, JPEG, JPE, JFIF, PNG, GIF, BMP, DIB, TIF, TIFF, WEBP, HEIC, HEIF, RAW, CR2, NEF, ARW, DNG, ORF, RW2, PSD, ICO, PCX, TGA
- **Video formats**: MP4, M4V, M4P, MOV, QT, AVI, WMV, ASF, FLV, F4V, MKV, WEBM, MPG, MPEG, MPE, 3GP, 3G2, VOB, OGV, MTS, M2TS, TS
- **Multiple date extraction methods**:
  1. EXIF DateTimeOriginal
  2. EXIF DateTime
  3. EXIF CreateDate
  4. Video metadata via ffprobe
  5. Filesystem timestamp (fallback)
- **Two interfaces**:
  - CLI (Command Line Interface) for advanced users
  - GUI (Graphical User Interface) for beginners
- **Test mode** - preview changes without actual renaming
- **Duplicate handling** - automatic counter suffix (_1, _2, etc.)
- **Real-time statistics** - progress tracking during processing
- **Threaded GUI** - non-blocking interface during processing
- Correct date format: `YYYY-MM-DD_HHmmss` (ISO 8601 compliant)
- Comprehensive documentation in Russian

### Technical
- Pure Python implementation
- Minimal dependencies (only Pillow required)
- Optional ffmpeg support for better video metadata extraction
- Cross-platform compatibility (Windows, Linux, macOS)
- Python 3.8+ support

## Comparison with Previous Solutions

| Feature | Other Solutions | Rename Media |
|---------|-----------------|--------------|
| Formats | ~8 | **49** |
| Interfaces | 1 | **2** (CLI + GUI) |
| Test mode | No | **Yes** |
| Fallback | No | **Yes** |
| Duplicate handling | No | **Yes** |
| Renamed file detection | No | **Yes** (v1.1) |
| Undo functionality | No | **Yes** (v1.4) |

---

[1.4.0]: https://github.com/maimik/rename-media/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/maimik/rename-media/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/maimik/rename-media/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/maimik/rename-media/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/maimik/rename-media/releases/tag/v1.0.0
