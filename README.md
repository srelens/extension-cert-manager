# cert-manager app for srelens

Declarative reference app for [srelens/srelens#582](https://github.com/srelens/srelens/issues/582).
It contains no app runtime, JavaScript bundle or Rust plugin.

This preview requires extension API `^0.7` and cert-manager's `cert-manager.io/v1` CRDs.
The exact tested host commit is in `compatibility.json`. Older srelens releases
do not support its configurable expiry card.

## What it shows

Certificates, Issuers, ClusterIssuers and CertificateRequests each have a resource
page. Certificates include Ready, Issuer and Not after columns and a panel with
validity, renewal time, issuer, destination Secret name and conditions. Issuing
takes precedence over Ready while a certificate is being reissued. Secret values
are never read.

The cluster dashboard counts certificates whose Not after is between now and
the selected expiry window. In app settings, choose 7, 14 (default), 30, 60 or 90
days. The card opens exactly the certificates it counted, with the same namespace
scope. Already expired certificates and certificates without a valid Not after
are outside this future window.

Renew requests the same `Issuing=True`, `ManuallyTriggered` status condition as
`cmctl renew`. The host confirms the specific cluster and Certificate and checks
its identity, version and preconditions before writing. An accepted request means
the controller was asked to reissue; resource status reports its progress. Renew
is unavailable while Issuing is already True.

## Installation and access

With a host supporting extension API `0.7`, open **Settings → Apps**, choose
**cert-manager**, and review the requested permissions before installing.
The catalog lists the signed [0.1.0 preview](https://github.com/srelens/extension-cert-manager/releases/tag/v0.1.0).
For local development, validate with the tested host below; unsigned development
copies must use an ID outside the reserved `org.srelens` namespace.

The app requests exactly `k8s.listCustomResource` and `k8s.setStatusCondition`.
Host discovery also needs access to CRD metadata. Kubernetes RBAC must allow:

- get/list/watch on certificates, issuers, clusterissuers and certificaterequests
  in the cert-manager.io group (clusterissuers are cluster scoped);
- get/list on customresourcedefinitions in apiextensions.k8s.io;
- patch on certificates/status for renewal;
- list on core events for the host's resource event panel, if desired.

No Secret read permission is needed. Keep RBAC scoped to the namespaces you use;
the installed app's permission grant does not replace Kubernetes authorization.

## Validate and package

Python 3, Node.js and the pinned host's Rust toolchain are sufficient. There are
no app dependencies to install.

```sh
python3 -m unittest discover -s tests
node --test tests/*.test.mjs
git clone https://github.com/srelens/srelens .host
git -C .host checkout "$(python3 -c 'import json; print(json.load(open("compatibility.json"))["hostRevision"])')"
python3 scripts/validate.py
python3 scripts/package.py --version 0.1.0
```

The validator checks the stable ID, exact host commit and actual Rust parser and
broker. Packaging preserves the manifest's exact bytes and writes SHA256SUMS.

The release workflow validates first, signs those bytes, checks the signature
against `signing-public.pem`, and publishes manifest.json, manifest.json.sig and
SHA256SUMS as immutable preview assets. Configure `APP_SIGNING_PRIVATE_KEY` with
the existing srelens app publisher key through GitHub's secret management. A
missing or mismatched key stops release; keys must never enter the repository.

## Live acceptance

Use an isolated cluster with cert-manager installed. The fixture
`tests/fixtures/self-signed.yaml` creates a dedicated namespace, local Issuer,
ClusterIssuer and three self-signed Certificates with 10, 20 and 40 day validity.
Controllers also create CertificateRequests.

Verify all four pages, Ready/Issuer/Not after columns, the certificate panel,
the 14-day count of one and 30-day count of two, matching card target lists,
and a confirmed Renew followed by an increased Certificate revision.
For developer testing only, an unsigned copy may use a nonreserved ID such as
`com.example.cert-manager`; signed catalog acceptance must use the original ID.
Keep issue 582 open until a catalog-installed signed release passes that check.
