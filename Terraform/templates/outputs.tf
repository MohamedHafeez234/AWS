output "instances_self_links" {
  description = "List of self-links for compute instances"
  value       = module.compute_instance.instances_self_links
}

output "instances_details" {
  description = "List of details for compute instances"
  value       = module.compute_instance.instances_details
}

output "available_zones" {
  description = "List of available zones in region"
  value       = module.compute_instance.available_zones
}

output "project_id" {
  description = "Project where compute instance was created"
  value       = data.google_project.env_project.project_id
}

output "region" {
  description = "Region where compute instance was created"
  value       = var.region
}
