# Changelog

## Unreleased

- Promoted the populated synthetic inbox workbench to the profile and social preview, with the full workbench and entry composition retained as complementary README images.
- Bound direct HTTP service to 64 concurrent workers with a 10-second socket deadline, and replace code-to-context nested rescans with merged linear context windows.

## 1.0.0 - 2026-08-09

- Rebuilt the original one-account CLI as a bilingual, responsive batch inbox workbench.
- Removed password authentication and arbitrary mail hosts; adopted Microsoft OAuth2/XOAUTH2 only.
- Added memory-only credential handling, safe error mapping, fixed network endpoints, same-origin checks, DNS-rebinding protection, request/rate/work limits, and redacted exports.
- Added contextual verification-code extraction, four global themes, synthetic demo data, favicon assets, local/server deployment, tests, CI, CodeQL, and release documentation.
