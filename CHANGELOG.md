# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0](https://github.com/hypn4/chzzk-python/compare/v0.4.2...v0.5.0) (2026-01-23)


### Features

* **ci:** add workflow_call trigger to CI workflow ([c7d016e](https://github.com/hypn4/chzzk-python/commit/c7d016e69a3af6cb79daf9fb1c528fd68c340861))
* **ci:** improve publish workflow reliability and trigger mechanism ([640b857](https://github.com/hypn4/chzzk-python/commit/640b857ac0033211bbf6bd3f35d82c242d0b8050))

## [0.4.2](https://github.com/hypn4/chzzk-python/compare/v0.4.1...v0.4.2) (2026-01-23)


### Bug Fixes

* **ci:** fetch all tags in publish workflow for hatch-vcs ([2b27204](https://github.com/hypn4/chzzk-python/commit/2b2720487a74d59ce563c1663f42520489f5d3cd))

## [0.4.1](https://github.com/hypn4/chzzk-python/compare/v0.4.0...v0.4.1) (2026-01-23)


### Bug Fixes

* **ci:** remove workflow_dispatch from publish workflow ([878def8](https://github.com/hypn4/chzzk-python/commit/878def8daa0aa582c0abe2b17d4d9408c5471ac5))

## [0.4.0](https://github.com/hypn4/chzzk-python/compare/v0.3.1...v0.4.0) (2026-01-23)


### Features

* **api:** add live status polling service ([5cede05](https://github.com/hypn4/chzzk-python/commit/5cede05360d4eb7b0c82d3939cf9577648307692))
* **chat:** add offline channel connection support ([5d63c34](https://github.com/hypn4/chzzk-python/commit/5d63c343786ce8d56be1676d298e5c9f3d4bc244))
* **chat:** add status monitoring and auto-reconnection ([6a77361](https://github.com/hypn4/chzzk-python/commit/6a77361f964015612266e3662c422904a8c9b16a))
* **cli:** add CLI module with auth, live, and chat commands ([98e3741](https://github.com/hypn4/chzzk-python/commit/98e37417a2bc9cb353d772037f73c81c3907e01b))
* **cli:** add CLI optional dependencies ([4cd1ca0](https://github.com/hypn4/chzzk-python/commit/4cd1ca0ccffd3b7dcc31984e0a17aceb3afc6480))
* **cli:** add interactive chat mode and offline support ([f6e173b](https://github.com/hypn4/chzzk-python/commit/f6e173b9f4abbcc4e8d2bcf3233ac126c20ccb7f))
* **exceptions:** add ChatReconnectError for reconnection failures ([a83a21d](https://github.com/hypn4/chzzk-python/commit/a83a21dd2a3b6a9e3ef274a8d98908e6dcfaaf35))
* **models:** add reconnection event models ([3d98b38](https://github.com/hypn4/chzzk-python/commit/3d98b387bdc1d09556d8eaee28277c7a6cf5b5f0))


### Bug Fixes

* **api:** update live detail endpoint to v3.3 ([0fc935b](https://github.com/hypn4/chzzk-python/commit/0fc935bc718124775ba6cc6198279d9909ba25aa))


### Documentation

* add CLI documentation to README ([348a2b7](https://github.com/hypn4/chzzk-python/commit/348a2b76ab47a79018010064db66fbd73c6347f1))
* **cli:** document interactive and offline chat flags ([b50f7a1](https://github.com/hypn4/chzzk-python/commit/b50f7a19fcad39ed110f963cab29300773b1ee01))

## [0.3.1](https://github.com/hypn4/chzzk-python/compare/v0.3.0...v0.3.1) (2026-01-23)


### Bug Fixes

* **ci:** add skip-existing to PyPI publish workflow ([84cce48](https://github.com/hypn4/chzzk-python/commit/84cce48))

## [0.3.0](https://github.com/hypn4/chzzk-python/compare/v0.2.0...v0.3.0) (2026-01-23)


### Features

* add unofficial API with Naver cookie authentication ([2481223](https://github.com/hypn4/chzzk-python/commit/2481223672b56c2de102d42fc4f17e7420e9df7a))


### Bug Fixes

* **ci:** trigger publish workflow from release-please ([d63302a](https://github.com/hypn4/chzzk-python/commit/d63302a61e683c73246e5fbd62b7e55cd7bfdd02))


### Documentation

* add unofficial API documentation to README ([0c7d575](https://github.com/hypn4/chzzk-python/commit/0c7d5756c6905ec9c4fa2715ffc3655516f9c1e3))
* add unofficial chat WebSocket protocol documentation ([bb2d4d3](https://github.com/hypn4/chzzk-python/commit/bb2d4d3d6fd058d365d8051169ba3318bdbc5c64))
* **examples:** add unofficial chat client examples ([8b68a41](https://github.com/hypn4/chzzk-python/commit/8b68a41964588ef40d4a5ce9cdd9bc4080cd5c09))

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
