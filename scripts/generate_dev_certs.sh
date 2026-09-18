#!/usr/bin/env bash
# Generates a self-signed CA + server certificate for LOCAL DEVELOPMENT ONLY.
# These files are never committed (see .gitignore) — every developer / CI
# environment must run this script once before enabling MTLS_ENABLED=true.
#
# Usage:
#   ./scripts/generate_dev_certs.sh
#
# Output (written to backend/certs/, all git-ignored):
#   ca.key, ca.pem         - self-signed development CA
#   server.key, server.pem - server certificate signed by the dev CA
#
# Do NOT use these certificates in production. Use a real CA / secrets
# manager (Vault, AWS ACM, cert-manager, etc.) for production deployments.

set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/backend/certs"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

echo "==> Generating development CA..."
openssl req -x509 -newkey rsa:2048 -days 365 -nodes \
  -keyout ca.key -out ca.pem \
  -subj "/CN=Vanguard Dev CA"

echo "==> Generating server key + CSR..."
openssl req -newkey rsa:2048 -nodes \
  -keyout server.key -out server.csr \
  -subj "/CN=vanguard-gateway.local"

echo "==> Signing server certificate with the dev CA..."
openssl x509 -req -in server.csr \
  -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out server.pem -days 365

rm -f server.csr

echo "==> Done. Certificates written to: $CERT_DIR"
echo "    Set MTLS_ENABLED=true in your .env to enable mTLS locally."
