variable "cloud_id" {
    default = "b1g66sjilsdsanah7cpe"
}

variable "folder_id" {
    default = "b1g0cnocne76e6s8gf33"
}

variable "zone" {
  default = "ru-central1-a"
}

variable "vm_name" {
  default = "lab04-vm"
}

variable "vm_user" {
  default = "e.s.belozerov"
}

variable "public_ssh_key" {
  description = "Path to public SSH key"
  type        = string
}