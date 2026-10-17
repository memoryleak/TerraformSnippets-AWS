#!/usr/bin/env bash
# Run bin/build.sh inside the Docker image, so only Docker is needed on the host.
#
# Usage: bin/docker-build.sh [--upgrade]
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
image="terraform-snippets-aws"

docker build --quiet --tag "$image" "$root" > /dev/null
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volume "$root:/work" \
  "$image" "$@"
