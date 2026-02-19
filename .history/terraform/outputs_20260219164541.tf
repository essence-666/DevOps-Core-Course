output "public_ip" {
  value = yandex_compute_instance.vm.id[0]
}
