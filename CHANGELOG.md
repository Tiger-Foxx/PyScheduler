# Changelog

All notable changes to PyScheduler - fox will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CLI interface for running tasks from command line
- Web dashboard for monitoring tasks
- Database persistence for task state
- Task dependency management

### Changed
- Improved error handling and retry logic
- Enhanced logging with structured output
- Better async task performance

## [1.0.0] - 2025-08-21

### Added
- **Core scheduler engine** with threading support
- **Task decorators**: `@task`, `@daily`, `@startup`, `@shutdown`
- **Multiple schedule types**: interval, CRON, daily, startup/shutdown
- **YAML configuration** support for production deployments
- **Priority system** with 5 levels (CRITICAL to IDLE)
- **Retry mechanism** with exponential backoff
- **Async task support** with native asyncio integration
- **Comprehensive logging** with configurable levels
- **Task statistics** and monitoring capabilities
- **Context manager** support for graceful shutdown
- **Timeout handling** for long-running tasks
- **Tag system** for task organization
- **Complete test suite** with >90% coverage
- **Extensive documentation** and examples

### Features
- Zero external dependencies for core functionality
- Optional dependencies for enhanced features (YAML, CRON, timezone)
- Thread-safe operations
- Graceful shutdown handling
- Production-ready configuration options
- Memory efficient execution
- Cross-platform compatibility (Windows, Linux, macOS)

### Examples
- Basic usage examples with common patterns
- Advanced usage with retry and error handling
- Configuration file examples for production
- CRON expression comprehensive guide
- Async task examples with aiohttp
- Error handling best practices

### Dependencies
- **Core**: Python 3.7+
- **Optional**: PyYAML (YAML config), pytz (timezone), croniter (CRON)
- **Development**: pytest, black, flake8, mypy

### Documentation
- Complete API reference
- Quick start guide (5-minute setup)
- Installation guide with all options
- Configuration guide for all features
- Troubleshooting guide for common issues
- Comprehensive examples library

## [0.9.0] - 2025-08-20 (Pre-release)

### Added
- Initial scheduler implementation
- Basic task management
- CRON expression support
- Threading executor

### Changed
- Refactored core architecture
- Improved task execution pipeline

## [0.1.0] - 2025-08-15 (Alpha)

### Added
- Project initialization
- Basic task scheduling prototype
- Initial documentation structure

---

**Note**: This project follows semantic versioning. 
- **Major** versions contain breaking changes
- **Minor** versions add new features (backward compatible)  
- **Patch** versions contain bug fixes and improvements
