# Toolchain for bin/build.sh: Terraform, Python 3 and Git.
# The repository is mounted at /work at run time, see bin/docker-build.sh.
FROM python:3.13-slim

ARG TERRAFORM_VERSION=1.16.6
ARG TARGETARCH

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git unzip \
 && cd /tmp \
 && curl -fsSLO "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${TARGETARCH}.zip" \
 && curl -fsSLO "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" \
 && grep "_linux_${TARGETARCH}.zip" "terraform_${TERRAFORM_VERSION}_SHA256SUMS" | sha256sum -c - \
 && unzip -q "terraform_${TERRAFORM_VERSION}_linux_${TARGETARCH}.zip" terraform -d /usr/local/bin \
 && rm -f terraform_* \
 && apt-get purge -y curl unzip \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# The container runs as the host user (see bin/docker-build.sh), which has no home directory in the image.
ENV HOME=/tmp \
    TF_IN_AUTOMATION=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /work
ENTRYPOINT ["bin/build.sh"]
