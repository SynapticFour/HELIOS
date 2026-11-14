# HELIOS

HELIOS writes a signed check trail for a pipeline whose export is already a file on disk. It does not call other programs to run that pipeline.

For someone who already has that export and wants the signature and the tamper check.

**Status: Early use.** Registry: HELIOS-MATURITY-001. Early use is the public label for the stage the claim calls early access. It is not a certification.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![CI](https://img.shields.io/github/actions/workflow/status/SynapticFour/HELIOS/ci.yml?branch=main)

Conformance of a running HTTP API stays in [Helix](https://github.com/SynapticFour/Helix) and [HelixTest](https://github.com/SynapticFour/HelixTest). How the two differ: [Helix vs HELIOS](https://github.com/SynapticFour/Helix/blob/main/docs/HELIX_VS_HELIOS.md).

## What it does

- It reads export JSON from disk and writes a signed check trail. It does not call other product APIs and it does not orchestrate them. Registry: TOOL-HELIOS-USE-001.
- `make prove` signs a fixture chain and rejects a tampered chain. No Nextflow and no network. Registry: TOOL-HELIOS-STATUS-001.
- The package name is `helios-audit`. PyPI `0.1.2` is the version in `pyproject.toml` and the version the 2026-10 registry query recorded. Git tag `v0.1.2` peels to `eda6417555052598650e0bafd3c230cd7b69f198`. This default branch is seven commits after that tag.

## Limits

- Early use is not general availability and not a certificate. Registry: HELIOS-MATURITY-001.
- The file it reads is an export already on disk. Registry: TOOL-HELIOS-USE-001.
- `make prove` is not a certification. The workflow that runs the tests does not start on every push. It starts when someone asks. Registry: TOOL-HELIOS-STATUS-001.
- Later commits on this default branch may be ahead of tag `v0.1.2` and of the PyPI line. `pip install helios-audit==0.1.2` matches the tag, not necessarily this commit.
- It does not check that a GA4GH HTTP service conforms. That is Helix and HelixTest.
- The dashboard (`make up`) is optional and needs `HELIOS_DASHBOARD_API_KEY`.

## Quick start

Prerequisites: Python 3.11 or newer.

```bash
pip install -e ".[dev]"
make prove
```

You should see `[prove] OK — valid chain signed; tamper rejected`.

A service you did not start is not required. The longer install is [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) and [docs/quickstart.md](docs/quickstart.md).

## Documentation

Every file under `docs/` is listed in [docs/README.md](docs/README.md). The groups are a tutorial, how-to guides, reference, and explanation.

### Tutorial

- [Getting started](docs/GETTING-STARTED.md)
- [Quickstart](docs/quickstart.md)

### How-to guides

- [Prove](docs/PROVE.md)
- [Operator](docs/operator.md)
- [Solum ingest](docs/solum-ingest.md)
- [Incident response](docs/INCIDENT_RESPONSE.md)

### Reference

- [For evaluators](docs/FOR-EVALUATORS.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Changelog](CHANGELOG.md)

### Explanation

- [Architecture](docs/ARCHITECTURE.md)
- [Decisions](docs/decisions/README.md)

## Licence

HELIOS is free to use under the Apache License 2.0, and you can read the source. Registry: TOOL-HELIOS-LICENSE-001. Not legal advice. The file is [LICENSE](LICENSE).

## Cite

Use [CITATION.cff](CITATION.cff). Prefer that file over a hand-copied line.

## Website

- Open tools: [https://synapticfour.com/en/offene-werkzeuge/](https://synapticfour.com/en/offene-werkzeuge/)
- Technical profile: [https://synapticfour.com/en/technical/code/](https://synapticfour.com/en/technical/code/)

The same pages exist in German (`/de/offene-werkzeuge/`, `/de/technik/code/`) and in French (`/fr/offene-werkzeuge/`, `/fr/technique/code/`).

The map of repositories: [profile/README.md](https://github.com/SynapticFour/.github/blob/main/profile/README.md).

Contact: [contact@synapticfour.com](mailto:contact@synapticfour.com)
