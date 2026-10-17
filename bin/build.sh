#!/usr/bin/env bash
# Regenerate all snippets from the AWS provider schema and docs.
#
# Usage: bin/build.sh [--upgrade]
#   --upgrade  move to the newest provider version allowed by bin/provider/versions.tf
#
# Requires: terraform, python3, git
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
provider_dir="$root/bin/provider"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

init_args=(-input=false)
if [[ "${1:-}" == "--upgrade" ]]; then
  init_args+=(-upgrade)
fi

terraform -chdir="$provider_dir" init "${init_args[@]}" > /dev/null
if [[ "${1:-}" == "--upgrade" ]]; then
  # Record checksums for every platform, otherwise each OS that runs the build would add its own to the lock file.
  terraform -chdir="$provider_dir" providers lock \
    -platform=linux_amd64 -platform=linux_arm64 \
    -platform=darwin_amd64 -platform=darwin_arm64 \
    -platform=windows_amd64 > /dev/null
fi
terraform -chdir="$provider_dir" providers schema -json > "$work/schema.json"
version="$(terraform -chdir="$provider_dir" version -json \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["provider_selections"]["registry.terraform.io/hashicorp/aws"])')"
echo "hashicorp/aws $version"

# Only the docs pages are needed, so fetch them sparsely at the matching tag.
git clone --quiet --depth 1 --filter=blob:none --sparse --branch "v$version" \
  https://github.com/hashicorp/terraform-provider-aws.git "$work/provider" 2> /dev/null
git -C "$work/provider" sparse-checkout set website/docs/r website/docs/d

python3 "$root/bin/generate.py" --schema "$work/schema.json" --docs "$work/provider/website/docs" --out "$root/Snippets"
python3 "$root/bin/check.py" "$root/Snippets"
