# Terraform Snippets AWS
Terraform snippets for Sublime Text 2/3 for the AWS provider.

## Requirements
Install package control by following instructions at https://packagecontrol.io/installation.

## Installation
Install `TerraformSnippets-AWS` with [Package Control](https://packagecontrol.io) and restart Sublime Text.


### Manual
Clone the repository in your Sublime Text "Packages" directory:

    git clone https://github.com/memoryleak/TerraformSnippets-AWS.git TerraformSnippets-AWS

The "Packages" directory is located at:

* OS X:
    `~/Library/Application Support/Sublime Text 3/Packages/`
* Linux:
    `~/.Sublime Text 3/Packages/`
* Windows:
    `%APPDATA%/Sublime Text 3/Packages/`

# Dependencies

- None

# Usage
In a `.tf` file type a resource or data source type and press <kbd>Tab</kbd>:

* `aws_instance` expands to `resource "aws_instance" "name" { ... }`
* `data_aws_ami` expands to `data "aws_ami" "name" { ... }`

Required arguments are tab stops. Optional arguments and blocks are listed as comments with a short description,
uncomment the ones you need.

# Generator
Snippets are generated from the AWS provider schema (`terraform providers schema -json`) and the provider's
documentation, so names, types and required/optional flags match the provider exactly.

Requirements: Docker, or Terraform, Python 3 and Git.

```
bin/docker-build.sh            # in Docker: regenerate for the provider version in bin/provider/.terraform.lock.hcl
bin/docker-build.sh --upgrade  # in Docker: move to the latest provider version first

bin/build.sh [--upgrade]       # the same, with the tools installed on the host
```

The Docker image (see `Dockerfile`) only holds the toolchain; the repository is mounted into it, so the snippets are
written straight into `Snippets/`. GitHub Actions runs the same image.

`bin/build.sh` dumps the schema, fetches the matching docs, runs `bin/generate.py` and validates the output with
`bin/check.py`. Do not edit files in `Snippets/` by hand, they are overwritten on every build.

The [Snippets workflow](.github/workflows/snippets.yml) checks on every pull request that the committed snippets
match the generator, and every Monday opens a pull request when a new AWS provider version is available.

# License

MIT

# Author Information

Haydar Ciftci <haydar.ciftci@gmail.com>
