# Yandex Cloud Infrastructure Deployment with Terraform

## Cloud Provider Selection
I chose Yandex Cloud because it was specified in the course requirements and provides free credits for students. It offers reliable infrastructure services in the Russian region.

## Terraform Version
```bash
❯ terraform --version
Terraform v1.5.7
on darwin_arm64
+ provider registry.terraform.io/yandex-cloud/yandex v0.187.0

Your version of Terraform is out of date! The latest version
is 1.14.5. You can update by downloading from https://www.terraform.io/downloads.html
```

## Resources Created
- **VM name**: lab04-vm
- **Region/Zone**: ru-central1-a
- **Platform**: Intel Ice Lake (standard-v1)
- **vCPU**: 2 cores 20 % (since the cheaper one)
- **RAM**: 1 GB 
- **Boot disk**: 10 GB (Ubuntu 22.04 LTS)
- **Network**: Custom VPC with public subnet
- **Security group**: With open ports 22 (only for my ip), 80, 5000

## Public IP Address
```
93.77.191.229
```

## SSH Connection Command
```bash
ssh -i ~/.ssh/id_ed25519 -l ubuntu 93.77.184.150
```

## Terraform Plan Output
```
terraform plan

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICmdbSKCFxCtdWPDN5DKaFsbrl1ZRDSWBZS2pQns/bM/ e.s.belozerov@macbook-RQM17PFPYP
            EOT
        }
      + name                      = "lab04-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = (known after apply)

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd84kp940dsrccckilj6"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }
    }

  # yandex_vpc_network.lab_network will be created
  + resource "yandex_vpc_network" "lab_network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab_sg will be created
  + resource "yandex_vpc_security_group" "lab_sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = -1
          + protocol       = "ANY"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }

      + ingress {
          + description    = "App port"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 5000
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "HTTP"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 80
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "SSH"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 22
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "188.130.155.165/32",
            ]
          + v6_cidr_blocks = []
        }
    }

  # yandex_vpc_subnet.lab_subnet will be created
  + resource "yandex_vpc_subnet" "lab_subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
~/uni/DevOps-Core-Course/terraform lab04 !1 ?2 ❯                                                                                                                   17:18:07
```

## Terraform Apply Output
```
❯ terraform apply

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be created
  + resource "yandex_compute_instance" "vm" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICmdbSKCFxCtdWPDN5DKaFsbrl1ZRDSWBZS2pQns/bM/ e.s.belozerov@macbook-RQM17PFPYP
            EOT
        }
      + name                      = "lab04-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v1"
      + status                    = (known after apply)
      + zone                      = (known after apply)

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd84kp940dsrccckilj6"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }
    }

  # yandex_vpc_network.lab_network will be created
  + resource "yandex_vpc_network" "lab_network" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = (known after apply)
      + name                      = "lab-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab_sg will be created
  + resource "yandex_vpc_security_group" "lab_sg" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = (known after apply)
      + name       = "lab-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = -1
          + protocol       = "ANY"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }

      + ingress {
          + description    = "App port"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 5000
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "HTTP"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 80
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks = []
        }
      + ingress {
          + description    = "SSH"
          + from_port      = -1
          + id             = (known after apply)
          + labels         = (known after apply)
          + port           = 22
          + protocol       = "TCP"
          + to_port        = -1
          + v4_cidr_blocks = [
              + "188.130.155.165/32",
            ]
          + v6_cidr_blocks = []
        }
    }

  # yandex_vpc_subnet.lab_subnet will be created
  + resource "yandex_vpc_subnet" "lab_subnet" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "lab-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.0.1.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

yandex_vpc_network.lab_network: Creating...
yandex_vpc_network.lab_network: Creation complete after 3s [id=enp63dqhauntlc50ddu4]
yandex_vpc_subnet.lab_subnet: Creating...
yandex_vpc_security_group.lab_sg: Creating...
yandex_vpc_subnet.lab_subnet: Creation complete after 0s [id=e9bqhbsacgdh594stfa8]
yandex_vpc_security_group.lab_sg: Creation complete after 2s [id=enpv8vdugs0i88u2ff7s]
yandex_compute_instance.vm: Creating...
yandex_compute_instance.vm: Still creating... [10s elapsed]
yandex_compute_instance.vm: Still creating... [20s elapsed]
yandex_compute_instance.vm: Still creating... [30s elapsed]
yandex_compute_instance.vm: Still creating... [40s elapsed]
yandex_compute_instance.vm: Still creating... [50s elapsed]
yandex_compute_instance.vm: Creation complete after 51s [id=fhm1qlo93vpmqmvjrkck]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

public_ip = "93.77.184.150"
~/uni/DevOps-Core-Course/terraform lab04 !1 ?2 ❯                                                                                                             1m 0s 17:19:35
```

## Proof of SSH Access

![ssh](./screenshots/ssh.png)

## Terrafrom destroy
```
❯ terraform destroy
yandex_vpc_network.lab_network: Refreshing state... [id=enp63dqhauntlc50ddu4]
yandex_vpc_subnet.lab_subnet: Refreshing state... [id=e9bqhbsacgdh594stfa8]
yandex_vpc_security_group.lab_sg: Refreshing state... [id=enpv8vdugs0i88u2ff7s]
yandex_compute_instance.vm: Refreshing state... [id=fhm1qlo93vpmqmvjrkck]

Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.vm will be destroyed
  - resource "yandex_compute_instance" "vm" {
      - created_at                = "2026-02-19T14:18:45Z" -> null
      - folder_id                 = "b1g0cnocne76e6s8gf33" -> null
      - fqdn                      = "fhm1qlo93vpmqmvjrkck.auto.internal" -> null
      - hardware_generation       = [
          - {
              - generation2_features = []
              - legacy_features      = [
                  - {
                      - pci_topology = "PCI_TOPOLOGY_V1"
                    },
                ]
            },
        ] -> null
      - id                        = "fhm1qlo93vpmqmvjrkck" -> null
      - labels                    = {} -> null
      - metadata                  = {
          - "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICmdbSKCFxCtdWPDN5DKaFsbrl1ZRDSWBZS2pQns/bM/ e.s.belozerov@macbook-RQM17PFPYP
            EOT
        } -> null
      - name                      = "lab04-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v1" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-a" -> null

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "fhmk9knek2me3k1lsl0e" -> null
          - disk_id     = "fhmk9knek2me3k1lsl0e" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size = 4096 -> null
              - image_id   = "fd84kp940dsrccckilj6" -> null
              - size       = 10 -> null
              - type       = "network-hdd" -> null
            }
        }

      - metadata_options {
          - aws_v1_http_endpoint = 1 -> null
          - aws_v1_http_token    = 2 -> null
          - gce_http_endpoint    = 1 -> null
          - gce_http_token       = 1 -> null
        }

      - network_interface {
          - index              = 0 -> null
          - ip_address         = "10.0.1.30" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:1d:57:09:1f" -> null
          - nat                = true -> null
          - nat_ip_address     = "93.77.184.150" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enpv8vdugs0i88u2ff7s",
            ] -> null
          - subnet_id          = "e9bqhbsacgdh594stfa8" -> null
        }

      - placement_policy {
          - host_affinity_rules       = [] -> null
          - placement_group_partition = 0 -> null
        }

      - resources {
          - core_fraction = 20 -> null
          - cores         = 2 -> null
          - gpus          = 0 -> null
          - memory        = 1 -> null
        }

      - scheduling_policy {
          - preemptible = false -> null
        }
    }

  # yandex_vpc_network.lab_network will be destroyed
  - resource "yandex_vpc_network" "lab_network" {
      - created_at                = "2026-02-19T14:18:39Z" -> null
      - default_security_group_id = "enpohhna9tmkh569c3r0" -> null
      - folder_id                 = "b1g0cnocne76e6s8gf33" -> null
      - id                        = "enp63dqhauntlc50ddu4" -> null
      - labels                    = {} -> null
      - name                      = "lab-network" -> null
      - subnet_ids                = [
          - "e9bqhbsacgdh594stfa8",
        ] -> null
    }

  # yandex_vpc_security_group.lab_sg will be destroyed
  - resource "yandex_vpc_security_group" "lab_sg" {
      - created_at = "2026-02-19T14:18:44Z" -> null
      - folder_id  = "b1g0cnocne76e6s8gf33" -> null
      - id         = "enpv8vdugs0i88u2ff7s" -> null
      - labels     = {} -> null
      - name       = "lab-sg" -> null
      - network_id = "enp63dqhauntlc50ddu4" -> null
      - status     = "ACTIVE" -> null

      - egress {
          - from_port      = -1 -> null
          - id             = "enpkos8fbdcv5ref1i8p" -> null
          - labels         = {} -> null
          - port           = -1 -> null
          - protocol       = "ANY" -> null
          - to_port        = -1 -> null
          - v4_cidr_blocks = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks = [] -> null
        }

      - ingress {
          - description    = "App port" -> null
          - from_port      = -1 -> null
          - id             = "enpo08kcb0g2edrkmo87" -> null
          - labels         = {} -> null
          - port           = 5000 -> null
          - protocol       = "TCP" -> null
          - to_port        = -1 -> null
          - v4_cidr_blocks = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks = [] -> null
        }
      - ingress {
          - description    = "HTTP" -> null
          - from_port      = -1 -> null
          - id             = "enpc7pat230ck8rea187" -> null
          - labels         = {} -> null
          - port           = 80 -> null
          - protocol       = "TCP" -> null
          - to_port        = -1 -> null
          - v4_cidr_blocks = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks = [] -> null
        }
      - ingress {
          - description    = "SSH" -> null
          - from_port      = -1 -> null
          - id             = "enpg3v816f87pk79jga1" -> null
          - labels         = {} -> null
          - port           = 22 -> null
          - protocol       = "TCP" -> null
          - to_port        = -1 -> null
          - v4_cidr_blocks = [
              - "188.130.155.165/32",
            ] -> null
          - v6_cidr_blocks = [] -> null
        }
    }

  # yandex_vpc_subnet.lab_subnet will be destroyed
  - resource "yandex_vpc_subnet" "lab_subnet" {
      - created_at     = "2026-02-19T14:18:42Z" -> null
      - folder_id      = "b1g0cnocne76e6s8gf33" -> null
      - id             = "e9bqhbsacgdh594stfa8" -> null
      - labels         = {} -> null
      - name           = "lab-subnet" -> null
      - network_id     = "enp63dqhauntlc50ddu4" -> null
      - v4_cidr_blocks = [
          - "10.0.1.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-a" -> null
    }

Plan: 0 to add, 0 to change, 4 to destroy.

Changes to Outputs:
  - public_ip = "93.77.184.150" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.vm: Destroying... [id=fhm1qlo93vpmqmvjrkck]
yandex_compute_instance.vm: Still destroying... [id=fhm1qlo93vpmqmvjrkck, 10s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhm1qlo93vpmqmvjrkck, 20s elapsed]
yandex_compute_instance.vm: Still destroying... [id=fhm1qlo93vpmqmvjrkck, 30s elapsed]
yandex_compute_instance.vm: Destruction complete after 35s
yandex_vpc_subnet.lab_subnet: Destroying... [id=e9bqhbsacgdh594stfa8]
yandex_vpc_security_group.lab_sg: Destroying... [id=enpv8vdugs0i88u2ff7s]
yandex_vpc_security_group.lab_sg: Destruction complete after 0s
yandex_vpc_subnet.lab_subnet: Destruction complete after 5s
yandex_vpc_network.lab_network: Destroying... [id=enp63dqhauntlc50ddu4]
yandex_vpc_network.lab_network: Destruction complete after 0s

Destroy complete! Resources: 4 destroyed.
~/uni/DevOps-Core-Course/terraform lab04 !1 ?2 ❯                                            49s 17:24:20
```
