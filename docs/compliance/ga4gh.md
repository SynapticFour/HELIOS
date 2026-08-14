# GA4GH Standards Coverage

HELIOS checks produce **orientation evidence** for GA4GH-related operational controls. They are not a GA4GH certification.

| HELIOS check/export | Intended alignment | What is actually proven |
|---|---|---|
| `reference_genome` | GRCh38 / Refget-style identity | Header M5/UR against a small built-in GRCh38 MD5 set |
| `container_pinning` | Reproducible runtimes | Digest pinning of discovered `container` refs; empty scan fails |
| `mane_transcripts` | Transcript reporting | Fraction of VCF transcript IDs present in a cached NCBI MANE list (gzip + optional MD5 sidecar) |
| `crypt4gh_output` | Crypt4GH 1.0 | 12-byte magic `crypt4gh\\x01\\x00\\x00\\x00` — suffixes are ignored |
| `rocrate` export | Portable provenance | RO-Crate 1.1 JSON-LD with canonical standard IRIs where known |

If a check cannot measure the property it names, it **fails or skips**. It does not pass.
