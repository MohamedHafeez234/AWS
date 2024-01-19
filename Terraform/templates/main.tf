locals {
  environment_code = element(split("", var.environment), 0)
}

resource "google_service_account" "compute_engine_service_account" {
  project      = data.google_project.env_project.project_id
  account_id   = "sa-example-app"
  display_name = "Example app service Account"
}

module "instance_template" {
  source       = "../../modules/instance_template"
  machine_type = var.machine_type
  region       = var.region
  project_id   = data.google_project.env_project.project_id
  subnetwork   = data.google_compute_subnetwork.subnetwork.self_link
  service_account = {
    email  = google_service_account.compute_engine_service_account.email
    scopes = ["compute-rw"]
  }
}

module "compute_instance" {
  source            = "../../modules/compute_instance"
  region            = var.region
  subnetwork        = data.google_compute_subnetwork.subnetwork.self_link
  num_instances     = var.num_instances
  hostname          = var.hostname
  instance_template = module.instance_template.self_link
}
