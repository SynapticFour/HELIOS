# ADR 0003 — Static copy of a signed report

- Status: Accepted
- Date: 2026-10-03

## Context

A public visitor must not receive the dashboard API key, and `/api/v1` stays authenticated. `/health` and `/static/*` are already reachable without that key. Those static files are the UI shell, not audit reports.

## Decision

`helios publish-report` is opt-in. It copies the newest JSON report from a reports directory into a directory the operator chooses. The copy is written only when the signature verifies against the trust store. A missing signature, an untrusted signer, or a file that contains the dashboard API key is refused and nothing is written. The command does not add a route and does not change dashboard auth.

## Consequences

Serving that directory is a separate static host. It is not the dashboard API. Unsigned reports stay off that host.
