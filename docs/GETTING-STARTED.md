# Getting started

HELIOS writes a signed check trail for a pipeline export that is already a file on disk. It does not call other programs to produce that file.

## Prerequisites

Python 3.11 or newer. The package name is `helios-audit`.

## In this repository

```bash
pip install -e ".[dev]"
make prove
```

You should see `[prove] OK — valid chain signed; tamper rejected` and a non-zero exit recorded for the tampered chain. `make prove` signs a fixture and rejects a tampered one. It does not run Nextflow and it does not use the network. The steps are in [PROVE.md](PROVE.md).

PyPI `helios-audit` 0.1.2 matches git tag `v0.1.2`. That tag peels to `eda6417555052598650e0bafd3c230cd7b69f198`. This default branch is `63c1c3cb86bd702e64d23d97502f8fe82a07e64c` (`v0.1.2-7-g63c1c3c`). `pip install helios-audit==0.1.2` matches the tag, not necessarily this commit. The version in `pyproject.toml` is still `0.1.2`.

## From the quickstart, after install

The longer install, including a dashboard, is [quickstart.md](quickstart.md). The commands there, after a clone:

```bash
helios init
export HELIOS_KEY_PASSPHRASE='use a real secret'
helios key generate
```

`helios init` copies `helios.toml.example`. An empty `checks.enabled` list is rejected. The example includes `ferrum_wes_outputs`: Ferrum WES outputs must be DRS ids. HELIOS does not call Ferrum.

`helios key generate` is passphrase-encrypted by default. Without `HELIOS_KEY_PASSPHRASE`, generation refuses unless you pass `--allow-unencrypted`, which is for a development machine only. Verification never trusts a PEM embedded in a report.

Wrapping a Nextflow run, and `helios report` / `helios validate`, are in [quickstart.md](quickstart.md). Exit 1 if any enabled check fails. A failed wrapped pipeline is not signed.

Optional dashboard: `make up` requires `HELIOS_DASHBOARD_API_KEY`. The page is `http://127.0.0.1:8765/static/index.html`.

Solum can write an export. HELIOS reads that file: `helios solum-audit --export …`. Notes: [operator.md](operator.md).
