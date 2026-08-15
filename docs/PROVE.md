# Prove HELIOS without a pipeline

`make prove` is the zero-risk path: unit tests plus a sign/tamper round-trip on a fixture chain. No Nextflow, no Ferrum, no network.

```bash
git clone https://github.com/SynapticFour/HELIOS.git && cd HELIOS
pip install -e ".[dev]"
make prove
```

What it demonstrates:

1. Subset checks run (`pytest` on signer + clinical access). The 80 % coverage gate is **`make test`**, not this subset.
2. A valid `solum-audit-helios-chain-v1` export is signed against a throwaway trust store.
3. The same export with a broken hash is **rejected** (non-zero exit).

GitHub Actions CI and the Release test job run the same `make prove` command.

That is HELIOS as a product. Optional joins:

| You have | Then |
|----------|------|
| A Nextflow/Snakemake work dir | `helios run --pipeline nextflow …` |
| A Solum sidecar export | `helios solum-audit --export file.json` |
| Ferrum WES artefacts | Hash them as `helios run` inputs — HELIOS does not call Ferrum APIs |

HELIOS is Apache-2.0. Install with `pip install helios-audit` ([helios-audit 0.1.0](https://pypi.org/project/helios-audit/0.1.0/); [RELEASING.md](../RELEASING.md)). Results are technical evidence, not certification.
