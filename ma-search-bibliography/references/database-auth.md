# Database Authentication Summary

Scopus:
- API key in `X-ELS-APIKey` header.
- Optional `X-ELS-Insttoken` if required by institution.

Embase:
- API key in `X-ELS-APIKey` header.
- Optional `X-ELS-Insttoken` and/or auth token if required.
- Access is provisioned case-by-case via Elsevier developer portal.

PubMed:
- `api_key` query parameter.

Cochrane ReviewDB:
- OAuth2 Bearer token or Basic auth.
