variable "environment" {
  description = "The environment the single project belongs to"
  type        = string
}

variable "vpc_type" {
  description = "The type of VPC to attach the project to. Possible options are base or restricted."
  type        = string
}

variable "region" {
  description = "The GCP region to create and test resources in"
  type        = string
  default     = "us-central1"
}

variable "num_instances" {
  description = "Number of instances to create"
  type        = number
}

variable "machine_type" {
  description = "Machine type to create, e.g. n1-standard-1"
  default     = "f1-micro"
}

variable "hostname" {
  description = "Hostname of instances"
  default     = "example-app"
}

variable "service_account" {
  default = null
  type = object({
    email  = string,
    scopes = set(string)
  })
  description = "Service account to attach to the instance. See https://www.terraform.io/docs/providers/google/r/compute_instance_template.html#service_account."
}

variable "folder_id" {
  description = "The folder id where project will be created"
  type        = string
}

variable "business_code" {
  description = "The code that describes which business unit owns the project"
  type        = string
  default     = "abcd"
}

variable "project_suffix" {
  description = "The name of the GCP project. Max 16 characters with 3 character business unit code."
  type        = string
}

variable "env_code" {
  description = "The environment code the single project belongs to, like 'd', 's', 'p'"
  type        = string
}
