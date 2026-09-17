# Data Sources

## Current status (this prototype)

| Source | Status | Data Type | Purpose |
|---|---|---|---|
| Demo Synthetic Provider | **DEMO** (active) | Synthetically generated cloud-structure imagery | Stand-in for INSAT/MOSDAC imagery |
| IMD Satellite (INSAT-3D/3DR) | **UNAVAILABLE** (not configured) | Real operational satellite products | Not implemented — see below |
| MOSDAC (ISRO) | **UNAVAILABLE** (not configured) | SST, OLR, QPE, Cloud Motion Vectors | Not implemented — see below |

No source in this build is ever reported as `CONNECTED` unless it genuinely
is — the `/api/data-sources` endpoint reflects real provider status, not a
simulated one.

## Why real sources aren't connected

1. **No internet access in the build/verification sandbox** used to
   construct this prototype — outbound requests to any external host
   (including IMD/MOSDAC endpoints, if they existed) were not possible to
   test.
2. **IMD and MOSDAC do not currently publish a public, credential-free
   imagery API** suitable for direct integration by a third-party hackathon
   prototype. Real integration would require a data-sharing agreement /
   registered access with these organizations.

## Provider abstraction

`backend/app/providers/base.py` defines a `SatelliteDataProvider` interface
implemented by:

- `DemoSatelliteProvider` — active, generates synthetic imagery.
- `IMDSatelliteProvider` — placeholder; raises `ProviderUnavailableError`
  until real credentials + an endpoint are wired in.
- `MOSDACProvider` — same, for ISRO's MOSDAC data.

Switching `SATELLITE_PROVIDER=imd` or `=mosdac` in `.env` without
implementing the real fetch logic will correctly surface a `503` error from
`/api/cyclones/<id>/satellite/frame` rather than silently falling back to
fake "live" data — this is intentional per the brief's requirement to never
substitute fake live data.

## Potential real sources for future integration

- INSAT-3D/3DR satellite imagery (IMD)
- MOSDAC (ISRO): SST, OLR, QPE, Cloud Motion Vectors, Water Vapour, Wind products
- IMD historical best-track cyclone data
- IBTrACS (international best-track archive) as an alternative historical
  source for track-forecast model training
