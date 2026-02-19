output "public_ip" {
  value = yandex_compute_instance.vm.network_interface.0.ip_address
}
