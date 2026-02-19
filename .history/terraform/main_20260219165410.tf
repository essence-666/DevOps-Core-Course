resource "yandex_vpc_network" "lab_network" {
  name = "lab-network"
}

resource "yandex_vpc_subnet" "lab_subnet" {
  name           = "lab-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.lab_network.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

resource "yandex_vpc_security_group" "lab_sg" {
  name       = "lab-sg"
  network_id = yandex_vpc_network.lab_network.id

  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "App port"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "yandex_compute_instance" "vm" {
  name = var.vm_name

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = "fd8kdq6d0p8sij7h5qe3" 
      size     = 10
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.lab_subnet.id
    security_group_ids = [yandex_vpc_security_group.lab_sg.id]
    nat                = true
  }

      metadata = {
    ssh-keys = "ubuntu:${file(var.public_ssh_key)}"
  }
}
