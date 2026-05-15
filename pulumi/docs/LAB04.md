First, i use the diffirent laptop to confirm pulumi part, since on my work laptop vpn is prohibited

## Pulumi Version and Language

* **Pulumi version**:
```
PS C:\Users\6ejlo\uni\DevOps-Core-Course\pulumi> pulumi version
v3.222.0
```
* **Language**: Go

## Code Differences from Terraform

* Infrastructure is defined using Go code instead of HCL.
* Resource creation is wrapped in `pulumi.Run` with `context`.
* Resources and arguments are Go structs (`VpcNetworkArgs`, `ComputeInstanceArgs`, etc.).
* Security rules are defined using arrays of structs (`IngressRuleArgs`, `EgressRuleArgs`).

## Advantages Discovered

* Code can use loops, functions, and variables directly.
* Type checking in Go helps avoid mistakes in resource parameters.
* Outputs can be exported programmatically and used in other Go code.
* Easier integration with external APIs and file reading.

## Challenges Encountered

* Initial issues with Go module imports and package paths.
* Pulumi requires correct JSON format for Yandex service account key.
* Struct fields differ from Terraform HCL blocks (Ingress/Egress rules, memory type, etc.).
* `Int` vs `Float64` type mismatch for memory resources.

## Terminal Output

### Pulumi Preview

```
PS C:\Users\6ejlo\uni\DevOps-Core-Course\pulumi> pulumi preview
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/essence-666-org/project/dev/previews/ebf20292-9889-4f48-a52d-262378464920

     Type                                  Name              Plan
 +   pulumi:pulumi:Stack                   project-dev       create
 +   ├─ pulumi:providers:yandex            yc                create
 +   ├─ yandex:index:VpcNetwork            lab-network       create
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg            create
 +   ├─ yandex:index:VpcSubnet             lab-subnet        create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-all-egress  create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-app         create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-http        create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-ssh         create
 +   └─ yandex:index:ComputeInstance       lab-vm            create
Outputs:
    public_ip: [unknown]

Resources:
    + 10 to create
```

### Pulumi Up

```
PS C:\Users\6ejlo\uni\DevOps-Core-Course\pulumi> pulumi up
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/essence-666-org/project/dev/previews/594eabdb-5ef5-4096-bd16-5cf3d1359ab5

     Type                                  Name              Plan
 +   pulumi:pulumi:Stack                   project-dev       create
 +   ├─ pulumi:providers:yandex            yc                create
 +   ├─ yandex:index:VpcNetwork            lab-network       create
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg            create
 +   ├─ yandex:index:VpcSubnet             lab-subnet        create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-all-egress  create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-app         create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-http        create
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-ssh         create
 +   └─ yandex:index:ComputeInstance       lab-vm            create
Outputs:
    public_ip: [unknown]

Resources:
    + 10 to create

Do you want to perform this update? details
+ pulumi:pulumi:Stack: (create)
    [urn=urn:pulumi:dev::project::pulumi:pulumi:Stack::project-dev]
    + pulumi:providers:yandex: (create)
        [urn=urn:pulumi:dev::project::pulumi:providers:yandex::yc]
        cloudId              : "b1g66sjilsdsanah7cpe"
        folderId             : "b1g0cnocne76e6s8gf33"
        serviceAccountKeyFile: "key.json"
        version              : "0.13.0"
        zone                 : "ru-central1-a"
    + yandex:index/vpcNetwork:VpcNetwork: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcNetwork:VpcNetwork::lab-network]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        name      : "lab-network"
    + yandex:index/vpcSecurityGroup:VpcSecurityGroup: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroup:VpcSecurityGroup::lab-sg]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        name      : "lab-sg"
        networkId : [unknown]
    + yandex:index/vpcSubnet:VpcSubnet: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSubnet:VpcSubnet::lab-subnet]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        name        : "lab-subnet"
        networkId   : [unknown]
        v4CidrBlocks: [
            [0]: "10.0.1.0/24"
        ]
        zone        : "ru-central1-a"
    + yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-all-egress]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        direction           : "egress"
        fromPort            : -1
        port                : -1
        protocol            : "ANY"
        securityGroupBinding: [unknown]
        toPort              : -1
        v4CidrBlocks        : [
            [0]: "0.0.0.0/0"
        ]
    + yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-app]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        description         : "App"
        direction           : "ingress"
        fromPort            : -1
        port                : 5000
        protocol            : "TCP"
        securityGroupBinding: [unknown]
        toPort              : -1
        v4CidrBlocks        : [
            [0]: "0.0.0.0/0"
        ]
    + yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-http]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        description         : "HTTP"
        direction           : "ingress"
        fromPort            : -1
        port                : 80
        protocol            : "TCP"
        securityGroupBinding: [unknown]
        toPort              : -1
        v4CidrBlocks        : [
            [0]: "0.0.0.0/0"
        ]
    + yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (create)
        [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-ssh]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        description         : "SSH"
        direction           : "ingress"
        fromPort            : -1
        port                : 22
        protocol            : "TCP"
        securityGroupBinding: [unknown]
        toPort              : -1
        v4CidrBlocks        : [
            [0]: "188.130.155.165/32"
        ]
    + yandex:index/computeInstance:ComputeInstance: (create)
        [urn=urn:pulumi:dev::project::yandex:index/computeInstance:ComputeInstance::lab-vm]
        [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::04da6b54-80e4-46f7-96ec-b56ff0331ba9]
        bootDisk               : {
            autoDelete      : true
            initializeParams: {
                imageId   : "fd84kp940dsrccckilj6"
                size      : 10
                type      : "network-hdd"
            }
        }
        metadata               : {
            ssh-keys  : "ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILPirly21NjP7vRbQxzV9aak+Zk4agARAw7jpXyS9C7/ 6ejlo@alohadance"
        }
        name                   : "lab-vm"
        networkAccelerationType: "standard"
        networkInterfaces      : [
            [0]: {
                ipv4            : true
                nat             : true
                securityGroupIds: [
                    [0]: [unknown]
                ]
                subnetId        : [unknown]
            }
        ]
        platformId             : "standard-v1"
        resources              : {
            coreFraction: 20
            cores       : 2
            memory      : 1
        }
        zone                   : "ru-central1-a"
    --outputs:--
    public_ip: [unknown]

Do you want to perform this update? yes
Updating (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/essence-666-org/project/dev/updates/5

     Type                                  Name              Status
 +   pulumi:pulumi:Stack                   project-dev       created (143s)
 +   ├─ pulumi:providers:yandex            yc                created (0.56s)
 +   ├─ yandex:index:VpcNetwork            lab-network       created (7s)
 +   ├─ yandex:index:VpcSubnet             lab-subnet        created (0.84s)
 +   ├─ yandex:index:VpcSecurityGroup      lab-sg            created (2s)
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-app         created (0.96s)
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-ssh         created (1s)
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-http        created (2s)
 +   ├─ yandex:index:VpcSecurityGroupRule  allow-all-egress  created (2s)
 +   └─ yandex:index:ComputeInstance       lab-vm            created (130s)
Outputs:
    public_ip: "89.169.133.198"

Resources:
    + 10 created

Duration: 2m27s
```

### SSH Connection to VM

```
ssh -l ubuntu 89.169.133.198
```

![ssh](./screenshots/ssh.png)

### VM Public IP Address

```
89.169.133.198 (will be deleted)
```

### Pulumi destroy
```
PS C:\Users\6ejlo\uni\DevOps-Core-Course\pulumi> pulumi destroy
Previewing destroy (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/essence-666-org/project/dev/previews/e1933499-99ea-4bbe-9a5a-d30a7d598f2e

     Type                                  Name              Plan
 -   pulumi:pulumi:Stack                   project-dev       delete
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-app         delete
 -   ├─ yandex:index:ComputeInstance       lab-vm            delete
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-ssh         delete
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-http        delete
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-all-egress  delete
 -   ├─ yandex:index:VpcSubnet             lab-subnet        delete
 -   ├─ yandex:index:VpcSecurityGroup      lab-sg            delete
 -   ├─ yandex:index:VpcNetwork            lab-network       delete
 -   └─ pulumi:providers:yandex            yc                delete
Outputs:
  - public_ip: "89.169.133.198"

Resources:
    - 10 to delete

Do you want to perform this destroy? details
- yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (delete)
    [id=enpv6504c4nf3ing8csb]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-app]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/computeInstance:ComputeInstance: (delete)
    [id=fhmt23sfc416dd8l9ko9]
    [urn=urn:pulumi:dev::project::yandex:index/computeInstance:ComputeInstance::lab-vm]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (delete)
    [id=enp8kpsfenu0fgojl7va]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-ssh]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (delete)
    [id=enpq61601fl08jvderd4]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-http]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule: (delete)
    [id=enpvnr031hkb34qoe480]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroupRule:VpcSecurityGroupRule::allow-all-egress]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcSubnet:VpcSubnet: (delete)
    [id=e9b6tlha48vpbcp8icdk]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSubnet:VpcSubnet::lab-subnet]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcSecurityGroup:VpcSecurityGroup: (delete)
    [id=enp5ej4a80ugh804rdfv]
    [urn=urn:pulumi:dev::project::yandex:index/vpcSecurityGroup:VpcSecurityGroup::lab-sg]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- yandex:index/vpcNetwork:VpcNetwork: (delete)
    [id=enp16oqts2c4nfpools0]
    [urn=urn:pulumi:dev::project::yandex:index/vpcNetwork:VpcNetwork::lab-network]
    [provider=urn:pulumi:dev::project::pulumi:providers:yandex::yc::7150d30e-bc1e-44e4-911a-80e433f8958a]
- pulumi:providers:yandex: (delete)
    [id=7150d30e-bc1e-44e4-911a-80e433f8958a]
    [urn=urn:pulumi:dev::project::pulumi:providers:yandex::yc]
- pulumi:pulumi:Stack: (delete)
    [urn=urn:pulumi:dev::project::pulumi:pulumi:Stack::project-dev]
    --outputs:--
  - public_ip: "89.169.133.198"

Do you want to perform this destroy? yes
Destroying (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/essence-666-org/project/dev/updates/6

     Type                                  Name              Status
 -   pulumi:pulumi:Stack                   project-dev       deleted (0.27s)
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-all-egress  deleted (5s)
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-ssh         deleted (6s)
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-app         deleted (6s)
 -   ├─ yandex:index:VpcSecurityGroupRule  allow-http        deleted (7s)
 -   ├─ yandex:index:ComputeInstance       lab-vm            deleted (39s)
 -   ├─ yandex:index:VpcSecurityGroup      lab-sg            deleted (0.91s)
 -   ├─ yandex:index:VpcSubnet             lab-subnet        deleted (5s)
 -   ├─ yandex:index:VpcNetwork            lab-network       deleted (1s)
 -   └─ pulumi:providers:yandex            yc                deleted (0.27s)
Outputs:
  - public_ip: "89.169.133.198"

Resources:
    - 10 deleted

Duration: 49s

The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained.
If you want to remove the stack completely, run `pulumi stack rm dev`.
PS C:\Users\6ejlo\uni\DevOps-Core-Course\pulumi>
```
