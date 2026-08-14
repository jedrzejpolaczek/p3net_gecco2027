# Security Policy

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report security issues by email to **jedrzej.polaczek@gmail.com** with the
subject line `[SECURITY] p3net — <short description>`.

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- Any suggested mitigations if known

You can expect an acknowledgement within 72 hours and a resolution timeline
after triage.

## Supported Versions

Only the latest commit on `main` is actively maintained. No stable release
exists yet.

## Scope

This is a research library implementing a black-box combinatorial
optimisation algorithm (P3Net). It has no network-facing components, does
not handle authentication, payment data, or personally identifiable
information. The primary security concern is dependency supply-chain risk.
