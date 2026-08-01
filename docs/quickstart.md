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

API routes under `/api/v1/*` require the key (`X-API-Key` or Bearer). `/health` and `/static/*` stay reachable so the UI can load and prompt for the key.

## 2) Initialize config

```bash
helios init
```

## 3) Generate signing keys

```bash
helios key generate
```

## 4) Wrap a Nextflow run

```bash
helios run --pipeline nextflow --work-dir ./work --output-dir ./results
```

## 5) Export report

```bash
helios report --run-id <run-id> --format json
```
