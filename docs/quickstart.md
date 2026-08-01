# Quickstart (5 minutes)

## 1) Install

HELIOS is **alpha** and is **not yet on PyPI**. Install from source:

```bash
git clone https://github.com/SynapticFour/HELIOS.git
cd HELIOS
pip install -e .
```

Or: `pip install "git+https://github.com/SynapticFour/HELIOS.git"`

HELIOS produces technical audit evidence; it is not a certification or legal determination.

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
