# Security Policy

## Supported Versions

Security fixes are provided for the latest published tag (`v0.1.1`). Treat `main` as ahead of the tag when they diverge.

## Reporting a Vulnerability

- Email: `contact@synapticfour.com`
- Include:
  - affected version
  - reproduction steps
  - potential impact
  - suggested remediation (if known)

Please do not open public issues for undisclosed vulnerabilities. We will acknowledge reports promptly and coordinate a responsible disclosure timeline.

## Supply chain

- On `v*` tags, the release workflow generates a CycloneDX SBOM and a lockfile attestation JSON (see [RELEASING.md](RELEASING.md)).
- Threat model: [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) · Incident response: [docs/INCIDENT_RESPONSE.md](docs/INCIDENT_RESPONSE.md).
