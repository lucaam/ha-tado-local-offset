# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-19

### Added
- Centralized helper functions `get_device_info()` and `get_climate_entity_id()` to reduce code duplication
- Added `TADO_MANUFACTURER` constant in const.py
- Comprehensive docstrings for all public and private methods
- Cross-field validation in config flow for preheat settings
- Energy-aware logging system with DEBUG and INFO levels
- `_parse_temperature()` helper method for consistent temperature parsing and error handling
- `_get_coordinator_for_entity()` helper function for service handlers

### Changed
- Refactored all platform files (climate, sensor, binary_sensor, number, switch) to use centralized `get_device_info()`
- Improved service handler implementations with better logging and error messages
- Enhanced coordinator logging with structured context for debugging
- Updated temperature validation with clearer clamping notifications

### Fixed
- Fixed logger initialization in coordinator (removed walrus operator anti-pattern)
- Fixed OptionsFlow configuration error by removing invalid `__init__` method
- Fixed AttributeError in `async_get_options_flow` by removing explicit config_entry parameter
- Improved error handling in temperature sensor parsing with detailed context logging

### Improved
- Code quality and maintainability through DRY principles
- Type hints coverage across all modules
- Error messages and logging consistency
- Removed hardcoded strings, replaced with constants

## [0.1.0] - Initial Release

### Initial Features
- Temperature compensation for Tado Smart Radiator Thermostats
- Window detection (sensor-based and temperature drop detection)
- Battery saver mode with configurable backoff timer
- Adaptive pre-heat learning
- HomeAssistant integration with climate, sensor, binary_sensor, number, and switch entities
