#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
TF_ROOT="${REPO_ROOT}/infrastructure/terraform"
TF_ENV="${TF_ROOT}/environments/dev"

echo "=====| Checking Terraform formatting |====="

terraform fmt \
  -check \
  -recursive \
  "${TF_ROOT}"

echo "=====| Preparing isolated Terraform validation environment |====="

VALIDATION_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${VALIDATION_DIR}"
}

trap cleanup EXIT

cp "${TF_ENV}"/*.tf "${VALIDATION_DIR}/"
cp "${TF_ENV}/.terraform.lock.hcl" "${VALIDATION_DIR}/"

echo "=====| Initialising providers without a backend |====="

terraform \
  -chdir="${VALIDATION_DIR}" \
  init \
  -backend=false \
  -input=false \
  -lockfile=readonly

echo "=====| Validating Terraform configuration |====="

terraform \
  -chdir="${VALIDATION_DIR}" \
  validate

echo "=====| Terraform static checks passed |====="