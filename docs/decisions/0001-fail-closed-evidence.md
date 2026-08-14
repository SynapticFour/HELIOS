# ADR 0001 — Fail-closed evidence

- Status: Accepted
- Date: 2026-08-15

## Context

HELIOS scores were used as if they were compliance grades. Several checks returned `pass` when they had not measured the named property (zero containers, Crypt4GH suffix, empty VUS, skip-only = 100).

## Decision

If a check cannot prove the property it names, it returns `fail` or `skip`. Skip is excluded from the score denominator. A suite with nothing scored is grade `N/A`, never 100. `helios run` exits 1 when any enabled check fails. Failed wrapped pipelines are not signed.

## Consequences

Existing “green” reports from earlier alphas are not comparable. Operators must name `checks.enabled`; an empty list is an error.
