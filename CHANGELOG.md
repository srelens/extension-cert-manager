# Changelog

## 0.2.0

Native Overview with certificate health, a configurable expiry-window count, upcoming expirations sorted earliest first, and issuer/request status.

Signed `.srelens-extension` packages now include the official project logo,
README and license, covered by the publisher signature and package checksum.
Manifest releases remain available. Update an existing manifest installation
to this version to install the packaged logo.

## 0.1.0

Preview declarative app for srelens extension API 0.7.

- Certificates, Issuers, ClusterIssuers and CertificateRequests pages.
- Ready and Issuing status, certificate expiry column and detail panel.
- Configurable future expiry window shared by the dashboard count and its linked list.
- Host-confirmed renewal through the Certificate status subresource.
- Signed, immutable manifest releases using the existing srelens publisher key.
