# GA4GH Standards Coverage

HELIOS aligns pipeline governance artifacts with core GA4GH standards.

## Check-to-standard mapping

| HELIOS check/export | GA4GH mapping | Practical evidence |
|---|---|---|
| `reference_genome` | Refget and GRCh38 migration recommendations | Sequence dictionary source and checksum evidence |
| `container_pinning` | TES/WES reproducibility expectations | Container digest pinning and immutable execution metadata |
| `mane_transcripts` | GKS and VRS-aligned reporting semantics | Transcript standardization evidence across variants |
| `crypt4gh_output` | Crypt4GH 1.0 | Encryption format detection on genomic outputs |
| `rocrate` export | Cloud Work Stream and WES metadata interoperability | Portable JSON-LD provenance package |

HELIOS therefore supports both run-time compliance checks and export-level interoperability aligned to GA4GH ecosystem expectations.

