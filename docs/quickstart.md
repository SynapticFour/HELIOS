# Quickstart (5 minutes)

## 1) Install

HELIOS is **alpha**. Install from source until `v0.1.0` is tagged and published; afterward `pip install helios-audit` works (see [RELEASING.md](../RELEASING.md)).

```bash
git clone https://github.com/SynapticFour/HELIOS.git
cd HELIOS
pip install -e .
```

Or: `pip install "git+https://github.com/SynapticFour/HELIOS.git"`

HELIOS produces technical audit evidence; it is not a certification or legal determination.

### Optional dashboard

```bash
export HELIOS_DASHBOARD_API_KEY=$(openssl rand -hex 32)
helios serve
# or: make up
```

API routes under `/api/v1/*` require the key (`X-API-Key` or Bearer). `/health` and `/static/*` stay reachable so the UI can load and prompt for the key. The UI keeps the key in memory, not `sessionStorage`. Compose binds `127.0.0.1:8765`.

## 2) Initialize config

```bash
helios init
```

This copies `helios.toml.example`. Empty `checks.enabled` is rejected — name the checks to run. Full key list: [operator.md](operator.md).

## 3) Generate signing keys

Passphrase-encrypted by default. Without `HELIOS_KEY_PASSPHRASE`, generation refuses unless you pass `--allow-unencrypted` (dev only).

```bash
export HELIOS_KEY_PASSPHRASE='use a real secret'
helios key generate
```

The matching `helios.pub` is the trust-store entry. Verification never trusts a PEM embedded in a report. See [ADR 0002](decisions/0002-trust-store.md).

## 4) Wrap a Nextflow run

```bash
helios run --pipeline nextflow --work-dir ./work --output-dir ./results
```

Exit **1** if any enabled check fails. Failed wrapped pipelines are not signed. `--no-sign` is explicit and still fails the process on check failures.

## 5) Export and validate

```bash
helios report --run-id <run-id> --format json
helios validate <run-id>
```

`validate` checks the signature against `trusted_keys_dir` (`*.pub`) and re-runs checks on stored paths. Exit 1 on an untrusted signature or a failed check.
