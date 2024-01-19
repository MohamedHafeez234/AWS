terraform {
  required_version = ">= 1.0.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 3.89"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 3.89"
    }
    null = {
      source = "hashicorp/null"
    }

    random = {
      source = "hashicorp/random"
    }
  }

  #  provider_meta "google" {
  #    module_name = "blueprints/terraform/terraform-example-foundation:app_env_base/v2.3.1"
  #  }
  #
  #  provider_meta "google-beta" {
  #    module_name = "blueprints/terraform/terraform-example-foundation:app_env_base/v2.3.1"
  #  }
}
