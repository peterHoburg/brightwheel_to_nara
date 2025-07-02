# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python script designed to transfer data from Brightwheel (https://schools.mybrightwheel.com) to Nara Baby Tracker (https://nara.com/pages/nara-baby-tracker). The project uses `uv` as the package manager and is structured as a Python package with a CLI entry point.

## Development Commands

### Setup and Dependencies
```bash
# Install dependencies
uv sync

# Create virtual environment and install in development mode
uv pip install -e .
```

### Running the Application
```bash
# Run via uv
uv run btn

# Or if installed
btn
```

### Package Management
```bash
# Add a dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Update dependencies
uv sync
```

## Project Structure

- `src/brightwheel_to_nara/` - Main package directory
  - `__init__.py` - Contains the `main()` function entry point
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions

## Architecture Notes

The project is currently a minimal skeleton with:
- A single entry point defined in `src/brightwheel_to_nara/__init__.py:main`
- A CLI command `btn` configured in `pyproject.toml` that calls the main function
- No external dependencies yet (empty dependencies list in pyproject.toml)

The intended functionality is to facilitate data migration between two childcare tracking platforms, likely involving:
- Authentication with both services
- Data extraction from Brightwheel
- Data transformation/mapping
- Data upload to Nara