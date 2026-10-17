# Pins the AWS provider version the snippets are generated from.
# The exact version is recorded in .terraform.lock.hcl; run `bin/build.sh --upgrade` to move it.
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}
