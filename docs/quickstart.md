# Quickstart (5 minutes)

## 1) Install

```bash
pip install helios-audit
```

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

