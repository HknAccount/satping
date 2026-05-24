# 🏗️ Terraform Cheat Sheet — SatPing Project

A complete guide to Terraform: what it is, every command, and how we used it.

---

## What is Terraform?

Terraform is an **Infrastructure as Code** tool.
Instead of logging into AWS and clicking buttons to create servers,
you write a file (.tf) describing what you want,
and Terraform creates it automatically on AWS.

**The big advantage:**
- Reproducible — run it again and get the exact same infrastructure
- Version controlled — tracked in Git like code
- Destroyable — one command deletes everything
- Documentable — the code IS the documentation

---

## How Terraform Works — The 3 Steps

```
Write .tf files  →  terraform plan  →  terraform apply  →  Infrastructure exists on AWS
                     (preview)          (create)

When done:       →  terraform destroy  →  Everything deleted, no more charges
```

---

## Complete Command Reference

### terraform init
```bash
terraform init
```
**What it does:** Downloads the AWS plugin (called a "provider") that Terraform needs to talk to AWS.
Run this ONCE when you first create a project, or after adding a new provider.
Creates a `.terraform` folder with the downloaded plugins.

Think of it like `npm install` or `pip install -r requirements.txt`.

---

### terraform plan
```bash
terraform plan
```
**What it does:** Previews what Terraform WILL create, change, or destroy — without actually doing anything.
Always run this before `apply` to check you're not accidentally deleting something.

Output example:
```
+ resource "aws_instance" "satping" {    # + means CREATE
    ami           = "ami-0302f42a44bf53a45"
    instance_type = "t3.micro"
}

Plan: 1 to add, 0 to change, 0 to destroy.
```

Symbols:
- `+` = will be CREATED
- `-` = will be DESTROYED
- `~` = will be MODIFIED

---

### terraform apply
```bash
terraform apply
```
**What it does:** Actually creates/modifies infrastructure on AWS.
Shows the plan first and asks you to type `yes` to confirm.

```bash
# Apply without asking for confirmation
terraform apply -auto-approve
```

After apply, Terraform saves the state to `terraform.tfstate`.

---

### terraform destroy
```bash
terraform destroy
```
**What it does:** Deletes EVERYTHING that Terraform created.
Always run this when you're done to avoid AWS charges.
Shows what will be destroyed and asks `yes` to confirm.

```bash
# Destroy without asking for confirmation
terraform destroy -auto-approve
```

---

### Other useful commands

```bash
# Show current state of infrastructure
terraform show

# Validate syntax of your .tf files (check for errors)
terraform validate

# Auto-format your .tf files neatly
terraform fmt

# See output values defined in your config
terraform output

# List all resources Terraform is managing
terraform state list

# See details of a specific resource
terraform state show aws_instance.satping

# Refresh state from real AWS (sync if someone changed things manually)
terraform refresh
```

---

## Our main.tf — Every Line Explained

```hcl
# ============================================================
# PROVIDER — tells Terraform which cloud to use
# ============================================================
provider "aws" {
  region = "eu-west-3"
  # eu-west-3 = Paris, France
  # Terraform reads AWS credentials from ~/.aws/credentials
  # (set up with: aws configure)
}


# ============================================================
# SECURITY GROUP — the firewall for our server
# ============================================================
resource "aws_security_group" "satping_sg" {
  # "aws_security_group" = type of resource
  # "satping_sg" = our internal name to reference this resource

  name        = "satping-sg"           # name shown in AWS console
  description = "Allow SSH"

  # INBOUND RULE — traffic coming INTO the server
  ingress {
    from_port   = 22           # SSH port
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    # 0.0.0.0/0 means "from ANY IP address on the internet"
    # In production you would restrict this to your own IP
  }

  # OUTBOUND RULE — traffic going OUT from the server
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"         # -1 means ALL protocols
    cidr_blocks = ["0.0.0.0/0"]
    # Allow server to reach anywhere (needed to pull Docker images, call APIs)
  }
}


# ============================================================
# EC2 INSTANCE — the virtual server
# ============================================================
resource "aws_instance" "satping" {
  # "aws_instance" = type of resource (EC2 virtual server)
  # "satping" = our internal name

  ami = "ami-0302f42a44bf53a45"
  # AMI = Amazon Machine Image
  # This is the "template" for the server — like choosing an OS
  # ami-0302f42a44bf53a45 = Amazon Linux 2023 in Paris (eu-west-3)
  # Different regions have different AMI IDs for the same OS

  instance_type = "t3.micro"
  # The size/power of the server
  # t3.micro = 2 vCPU, 1GB RAM — smallest option, free tier eligible
  # Other options: t3.small (2GB), t3.medium (4GB), t3.large (8GB)

  key_name = "satping-key"
  # The SSH key pair to use for login
  # Must already exist in AWS (created manually in EC2 → Key Pairs)

  vpc_security_group_ids = [aws_security_group.satping_sg.id]
  # Attach the security group we created above
  # aws_security_group.satping_sg.id = reference to the ID of our security group
  # Terraform resolves this automatically — it knows the ID after creating the SG

  tags = {
    Name = "satping-server"
    # Tags are labels — Name tag is shown in AWS console
    # You can add more tags: Environment = "dev", Project = "satping"
  }
}
```

---

## What is terraform.tfstate?

After `terraform apply`, Terraform creates a file called `terraform.tfstate`.

This file tracks:
- What resources exist on AWS
- Their IDs, IPs, and all properties
- So Terraform knows what to update or destroy next time

**Rules:**
- NEVER delete this file manually
- NEVER push it to GitHub (it contains sensitive data)
- It is protected in our `.gitignore`

If you lose this file, Terraform loses track of your infrastructure.
You would have to manually destroy resources in the AWS console.

---

## Terraform Workflow for This Project

```bash
# First time setup
cd D:\proj\devops_satping\terraform
terraform init

# Every time you make changes
terraform plan          # check what will happen
terraform apply         # create/update infrastructure
                        # type "yes" when prompted

# Get your server's IP after creation
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=satping-server" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text

# When finished working (to avoid charges)
terraform destroy       # type "yes" when prompted

# Next day — recreate everything in 13 seconds
terraform apply         # type "yes"
```

---

## AWS Regions Cheat Sheet

| Region Code | Location |
|-------------|----------|
| eu-west-3 | Paris, France ← we used this |
| eu-west-1 | Ireland |
| eu-central-1 | Frankfurt, Germany |
| us-east-1 | North Virginia, USA |
| us-west-2 | Oregon, USA |
| ap-southeast-1 | Singapore |

Choose the region closest to your users for lowest latency.

---

## Instance Types Cheat Sheet

| Type | vCPU | RAM | Use case |
|------|------|-----|----------|
| t3.micro | 2 | 1 GB | Free tier, tiny apps ← we used this |
| t3.small | 2 | 2 GB | Kubernetes (minimum) |
| t3.medium | 2 | 4 GB | Small production apps |
| t3.large | 2 | 8 GB | Medium production apps |

---

## Common Terraform Errors and Fixes

### Error: No valid credentials
```
Error: No valid credential sources found
```
Fix: Run `aws configure` and enter your Access Key and Secret Key.

### Error: Instance type not eligible for Free Tier
```
InvalidParameterCombination: The specified instance type is not eligible for Free Tier
```
Fix: Change `instance_type` from `t2.micro` to `t3.micro` in eu-west-3.

### Error: AMI not found
```
Error: InvalidAMIID.NotFound
```
Fix: AMI IDs are region-specific. Find the correct AMI ID for your region in AWS console → EC2 → AMIs.

### Error: KeyPair not found
```
Error: InvalidKeyPair.NotFound
```
Fix: Create the key pair first in AWS console → EC2 → Key Pairs, then reference its name in Terraform.
