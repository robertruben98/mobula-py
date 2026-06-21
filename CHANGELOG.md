# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-21

### Added

- Initial release.
- Synchronous `MobulaClient` and asynchronous `AsyncMobulaClient`.
- Endpoints: `get_market_data`, `get_multi_market_data`, `get_metadata`,
  `get_market_history`, `get_blockchains`, `get_wallet_portfolio`,
  `get_wallet_transactions`.
- Configurable `api_key` (sent in the `Authorization` header), `base_url`,
  `timeout`, `max_retries`, and `backoff_factor`.
- Automatic retry with exponential backoff on HTTP 429 / 5xx, honouring
  `Retry-After`.
- Typed pydantic v2 models with `extra="allow"`; ships `py.typed`.
- Exception hierarchy: `MobulaError`, `MobulaAPIError`, `MobulaAuthError`,
  `MobulaRateLimitError`.

[Unreleased]: https://github.com/robertruben98/mobula-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/robertruben98/mobula-py/releases/tag/v0.1.0
