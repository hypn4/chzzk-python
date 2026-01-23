# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1](https://github.com/hypn4/chzzk-python/compare/v0.2.0...v0.2.1) (2026-01-23)


### Bug Fixes

* **ci:** trigger publish workflow from release-please ([d63302a](https://github.com/hypn4/chzzk-python/commit/d63302a61e683c73246e5fbd62b7e55cd7bfdd02))

## [0.2.0](https://github.com/hypn4/chzzk-python/compare/v0.1.0...v0.2.0) (2026-01-23)


### Features

* **ci:** add Release Please workflow for automated releases ([34be227](https://github.com/hypn4/chzzk-python/commit/34be227f6f75fe769f0a3760673520487b7dd004))

## [Unreleased]

### Added

- **exceptions**: Add custom exception classes for Chzzk SDK
- **http**: Add HTTP client wrapper for Chzzk API
- **auth**: Add OAuth authentication models
- **auth**: Add token storage implementations
- **auth**: Add OAuth client implementations
- **examples**: Add OAuth authorization code flow example
- **examples**: Enhance OAuth server with ChzzkClient and API demos
- **http**: Add PUT, PATCH, and DELETE methods to HTTP clients
- **http**: Add Open API endpoint constants
- **models**: Add Pydantic models for Chzzk API responses
- **api**: Implement service layer for Chzzk Open API
- **client**: Add unified Chzzk API client
- Export client, services, and models from package root
- **http**: Add params support to POST methods
- **models**: Add session and realtime event models
- **http**: Add session API endpoints
- **exceptions**: Add session-related exceptions
- **api**: Implement session service for WebSocket management
- **realtime**: Add Socket.IO client for realtime events
- **client**: Integrate session service and event client
- Export session, realtime, and related components
- **examples**: Add session list endpoint to OAuth server
- **examples**: Add realtime and session management examples

### Build

- Add python-socketio dependency for realtime events
- Add websocket-client dependency
- Exclude AI tooling files from git and distribution

### Changed

- **auth**: Remove get_access_token method from OAuth classes

### Documentation

- Add comprehensive SDK documentation

### Fixed

- **http**: Extract content field from Chzzk API response wrapper
- **realtime**: Handle string and dict event data from Socket.IO
- **models**: Make user_role_code optional in ChatEvent

### Testing

- **auth**: Add comprehensive OAuth test suite
- Add comprehensive test suite for API services and client
- Add tests for session service and realtime client

[Unreleased]: https://github.com/hypn4/chzzk-python/compare/...HEAD
