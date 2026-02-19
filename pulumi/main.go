package main

import (
	"github.com/pulumi/pulumi-yandex/sdk/go/yandex"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {

		zone := "ru-central1-a"

		provider, err := yandex.NewProvider(ctx, "yc", &yandex.ProviderArgs{
			ServiceAccountKeyFile: pulumi.String("key.json"),
			CloudId:               pulumi.String("b1g66sjilsdsanah7cpe"),
			FolderId:              pulumi.String("b1g0cnocne76e6s8gf33"),
			Zone:                  pulumi.String(zone),
		})
		if err != nil {
			return err
		}

		// ---------------- NETWORK ----------------

		network, err := yandex.NewVpcNetwork(ctx, "lab-network",
			&yandex.VpcNetworkArgs{
				Name: pulumi.String("lab-network"),
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		subnet, err := yandex.NewVpcSubnet(ctx, "lab-subnet",
			&yandex.VpcSubnetArgs{
				Name:         pulumi.String("lab-subnet"),
				Zone:         pulumi.String(zone),
				NetworkId:    network.ID(),
				V4CidrBlocks: pulumi.StringArray{pulumi.String("10.0.1.0/24")},
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// ---------------- SECURITY GROUP ----------------

		sg, err := yandex.NewVpcSecurityGroup(ctx, "lab-sg",
			&yandex.VpcSecurityGroupArgs{
				Name:      pulumi.String("lab-sg"),
				NetworkId: network.ID(),
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// SSH rule
		_, err = yandex.NewVpcSecurityGroupRule(ctx, "allow-ssh",
			&yandex.VpcSecurityGroupRuleArgs{
				SecurityGroupBinding: sg.ID(),
				Direction:            pulumi.String("ingress"),
				Protocol:             pulumi.String("TCP"),
				Port:                 pulumi.Int(22),
				V4CidrBlocks: pulumi.StringArray{
					pulumi.String("188.130.155.165/32"),
				},
				Description: pulumi.String("SSH"),
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// HTTP rule
		_, err = yandex.NewVpcSecurityGroupRule(ctx, "allow-http",
			&yandex.VpcSecurityGroupRuleArgs{
				SecurityGroupBinding: sg.ID(),
				Direction:            pulumi.String("ingress"),
				Protocol:             pulumi.String("TCP"),
				Port:                 pulumi.Int(80),
				V4CidrBlocks: pulumi.StringArray{
					pulumi.String("0.0.0.0/0"),
				},
				Description: pulumi.String("HTTP"),
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// App rule
		_, err = yandex.NewVpcSecurityGroupRule(ctx, "allow-app",
			&yandex.VpcSecurityGroupRuleArgs{
				SecurityGroupBinding: sg.ID(),
				Direction:            pulumi.String("ingress"),
				Protocol:             pulumi.String("TCP"),
				Port:                 pulumi.Int(5000),
				V4CidrBlocks: pulumi.StringArray{
					pulumi.String("0.0.0.0/0"),
				},
				Description: pulumi.String("App"),
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// Egress allow all
		_, err = yandex.NewVpcSecurityGroupRule(ctx, "allow-all-egress",
			&yandex.VpcSecurityGroupRuleArgs{
				SecurityGroupBinding: sg.ID(),
				Direction:            pulumi.String("egress"),
				Protocol:             pulumi.String("ANY"),
				V4CidrBlocks: pulumi.StringArray{
					pulumi.String("0.0.0.0/0"),
				},
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		// ---------------- SSH KEY ----------------

		pubKey := "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILPirly21NjP7vRbQxzV9aak+Zk4agARAw7jpXyS9C7/ 6ejlo@alohadance"

		// ---------------- VM ----------------

		vm, err := yandex.NewComputeInstance(ctx, "lab-vm",
			&yandex.ComputeInstanceArgs{
				Name: pulumi.String("lab-vm"),
				Zone: pulumi.String(zone),

				Resources: &yandex.ComputeInstanceResourcesArgs{
					Cores:        pulumi.Int(2),
					Memory: 	  pulumi.Float64(1),
					CoreFraction: pulumi.Int(20),
				},

				BootDisk: &yandex.ComputeInstanceBootDiskArgs{
					InitializeParams: &yandex.ComputeInstanceBootDiskInitializeParamsArgs{
						ImageId: pulumi.String("fd84kp940dsrccckilj6"),
						Size:    pulumi.Int(10),
						Type:    pulumi.String("network-hdd"),
					},
				},

				NetworkInterfaces: yandex.ComputeInstanceNetworkInterfaceArray{
					&yandex.ComputeInstanceNetworkInterfaceArgs{
						SubnetId:         subnet.ID(),
						SecurityGroupIds: pulumi.StringArray{sg.ID()},
						Nat:              pulumi.Bool(true),
					},
				},

				Metadata: pulumi.StringMap{
					"ssh-keys": pulumi.String("ubuntu:" + string(pubKey)),
				},
			},
			pulumi.Provider(provider))
		if err != nil {
			return err
		}

		ctx.Export("public_ip",
			vm.NetworkInterfaces.Index(pulumi.Int(0)).NatIpAddress())

		return nil
	})
}
