# 🛰️ SatPing — Complete Beginner-Friendly Documentation

This document explains **every tool, every command, and every decision** made in this project.
Written so that even a non-technical person can understand what each part does and why.

---

## 🖥️ What Operating System Did We Use?

| Where | OS |
|-------|----|
| My development machine | **Windows 11** |
| AWS Server in the cloud | **Amazon Linux 2023** (Linux) |
| Running Ansible commands | **WSL — Windows Subsystem for Linux** (Ubuntu inside Windows) |

**Why Linux on the server?**
Almost all cloud servers run Linux. It is free, stable, lightweight, and the industry standard for servers.
Windows servers exist but are rarely used in DevOps.

**Why WSL for Ansible?**
Ansible is a Linux tool. It does not run natively on Windows.
WSL lets us run Ubuntu (Linux) inside Windows without a separate machine.

---

## 🌐 Networking — VPC, Public & Private

### What is a VPC?
VPC = Virtual Private Cloud. It is your own private network inside AWS.
Think of it like a house — AWS gives you a house (VPC) and you decide which rooms (subnets) are public or private.

### What did we use in this project?
We used the **default VPC** that AWS creates automatically. It includes:
- A **public subnet** — our EC2 server is here, accessible from the internet
- An **internet gateway** — allows traffic in and out

### Security Group — the firewall
We created a Security Group in Terraform that acts as a firewall:

```hcl
resource "aws_security_group" "satping_sg" {
  name        = "satping-sg"
  description = "Allow SSH"

  # INBOUND — who can connect TO our server
  ingress {
    from_port   = 22        # port 22 = SSH (remote login)
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # from anywhere on the internet
  }

  # OUTBOUND — our server can connect to anything
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"           # all protocols
    cidr_blocks = ["0.0.0.0/0"]  # to anywhere
  }
}
```

**In plain English:**
- We only opened port 22 (SSH) so we can log into our server remotely
- The server can reach the internet (to pull Docker images, call APIs)
- Everything else is blocked by default

**In a production system** you would also:
- Create a private subnet for databases (not accessible from internet)
- Only open specific ports needed by your app
- Use a bastion host (jump server) instead of direct SSH

---

## 🐍 Python — The Application

### What it does:
Calls the N2YO API every 60 seconds to get a list of satellites currently flying above Paris.
Prints their name, latitude, longitude and altitude.
Also exposes a metrics endpoint on port 8000 for Prometheus to read.

### Key commands:
```bash
# Install the requests library
pip install requests

# Run the script locally
python main.py

# Install all libraries from requirements file
pip install -r requirements.txt
```

### What is requirements.txt?
A file listing all Python libraries the app needs:
```
requests          # makes HTTP calls to the N2YO API
prometheus-client # exposes metrics on port 8000
```
Instead of running `pip install x` for every library, you write them all here
and run `pip install -r requirements.txt` once.

---

## 🐳 Docker — Packaging the App

### What is Docker?
Imagine you baked a cake on your computer.
Without Docker: "it works on my machine" — nobody else can eat your cake unless they have the exact same oven, ingredients, temperature.
With Docker: you ship the cake already baked in a sealed box. Anyone can open the box and eat it — on any machine, any server, any cloud.

### What is a Dockerfile?
A recipe that tells Docker how to build your app's box (called an image):

```dockerfile
FROM python:3.12-slim      # start from an official Python box

WORKDIR /app               # go into the /app folder inside the box

COPY requirements.txt .    # copy requirements file into the box
RUN pip install -r requirements.txt  # install libraries inside the box

COPY main.py .             # copy our Python script into the box

CMD ["python", "main.py"]  # when the box starts, run this command
```

### Docker commands explained:

```bash
# BUILD — create the image (the sealed box) from your Dockerfile
docker build -t satping .
# -t satping = name the image "satping"
# . = use the current folder to find the Dockerfile

# RUN — start a container (a running instance of the box)
docker run -e N2YO_API_KEY=your_key satping
# -e = pass an environment variable (the API key) into the container
# satping = which image to run

# Run in background (detached mode)
docker run -d --name satping -e N2YO_API_KEY=your_key satping
# -d = run in background
# --name satping = give the container the name "satping"

# See running containers
docker ps

# See container logs (output)
docker logs satping
docker logs -f satping    # -f = follow live (like tail -f)

# Stop a container
docker stop satping

# Remove a container
docker rm satping

# See all images
docker images
```

### What is Docker Compose?
When you need to run multiple containers together (our app + Prometheus + Grafana),
Docker Compose starts them all with one command and lets them talk to each other.

```bash
# Start all services defined in docker-compose.yml
docker compose up

# Start and rebuild images first
docker compose up --build

# Stop all services
docker compose down

# See logs of all services
docker compose logs -f
```

---

## 🐙 Git & GitHub — Version Control

### What is Git?
Git tracks every change you make to your code. Like "track changes" in Word but for code.
You can go back to any previous version, collaborate with others, and never lose work.

### Commands explained:

```bash
# Start tracking a folder with Git
git init

# See what files changed
git status

# Stage files to be saved (add to the next snapshot)
git add .               # add ALL changed files
git add main.py         # add only one specific file

# Save a snapshot with a message explaining what changed
git commit -m "add Dockerfile"

# Connect to GitHub (only once)
git remote add origin https://github.com/HknAccount/satping.git

# Push your commits to GitHub
git push

# First push (sets the upstream branch)
git push -u origin main

# Pull latest changes from GitHub
git pull

# See history of all commits
git log --oneline
```

### What is .gitignore?
A file that tells Git which files to NEVER push to GitHub.
We never push secrets, API keys, or temporary files:

```
.env                          # contains our real API key
terraform/terraform.tfstate   # contains sensitive AWS info
terraform/.terraform/         # large temporary folder
__pycache__/                  # Python temporary files
```

---

## ⚙️ GitHub Actions — Automatic CI/CD

### What is CI/CD?
CI = Continuous Integration — automatically test code when you push
CD = Continuous Deployment — automatically deploy when tests pass

### What happens:
Every time you run `git push`, GitHub automatically:
1. Spins up a fresh Linux machine (ubuntu-latest)
2. Downloads your code
3. Installs Python
4. Installs your libraries
5. Builds your Docker image
6. Runs your container to verify it works
7. Shows green ✅ or red ❌

### The pipeline file (.github/workflows/ci.yml):
```yaml
name: SatPing CI

on:
  push:                    # trigger: when code is pushed
    branches: [ main ]     # only on the main branch

jobs:
  build:
    runs-on: ubuntu-latest  # use a fresh Ubuntu machine

    steps:
      - name: Checkout code
        uses: actions/checkout@v3       # download the code

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'        # install Python 3.12

      - name: Install dependencies
        run: pip install -r requirements.txt   # install libraries

      - name: Build Docker image
        run: docker build -t satping .         # build the image

      - name: Run SatPing
        env:
          N2YO_API_KEY: ${{ secrets.N2YO_API_KEY }}  # read from GitHub Secrets
        run: docker run -e N2YO_API_KEY=$N2YO_API_KEY satping
```

### GitHub Secrets:
Instead of putting your API key directly in the file (dangerous!),
you store it in GitHub Settings → Secrets.
GitHub injects it into the pipeline automatically. Nobody can see it.

---

## ☁️ AWS — Amazon Web Services

### What is AWS?
AWS is a cloud provider — they have massive data centers around the world.
Instead of buying a physical server, you rent one from AWS and pay per hour.
We used the Paris region (eu-west-3) to minimize latency.

### What AWS services did we use?

| Service | What it does |
|---------|--------------|
| **EC2** | Virtual server (our Linux machine in the cloud) |
| **ECR** | Docker image storage (like DockerHub but private on AWS) |
| **IAM** | User permissions and access keys |
| **Security Groups** | Firewall rules for our server |
| **Default VPC** | Our private network in AWS |

### AWS CLI commands used:

```bash
# Configure your AWS credentials
aws configure
# Asks for: Access Key ID, Secret Access Key, Region, Output format

# Check your identity
aws sts get-caller-identity

# List S3 buckets (test credentials work)
aws s3 ls

# Get your server's public IP
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=satping-server" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text

# Login to ECR (Docker registry on AWS)
aws ecr get-login-password --region eu-west-3 | \
  docker login --username AWS --password-stdin \
  439638384547.dkr.ecr.eu-west-3.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name satping --region eu-west-3
```

---

## 🏗️ Terraform — Infrastructure as Code

### What is Terraform?
Instead of logging into AWS console and clicking buttons to create servers,
you write a file describing what you want, and Terraform creates it automatically.

**Without Terraform:** click → click → click → forget what you clicked → can't reproduce
**With Terraform:** write once → run command → server exists → destroy when done → recreate anytime

### How Terraform works:

```
You write .tf files  →  terraform plan  →  terraform apply  →  Real infrastructure on AWS
                         (preview)          (create)
```

### Complete Terraform commands:

```bash
# 1. INIT — download the AWS provider plugin (run once per project)
terraform init
# Like npm install or pip install — downloads dependencies

# 2. PLAN — preview what will be created/changed/destroyed
terraform plan
# Shows you exactly what Terraform WILL do before doing it
# Always run this before apply!
# Output: "Plan: 1 to add, 0 to change, 0 to destroy"

# 3. APPLY — actually create the infrastructure on AWS
terraform apply
# Terraform shows the plan again and asks "yes/no"
# Type "yes" to confirm
# Creates your real server on AWS

# Apply without asking for confirmation (for automation)
terraform apply -auto-approve

# 4. DESTROY — delete everything Terraform created
terraform destroy
# Type "yes" to confirm
# Destroys all resources to avoid AWS charges
# IMPORTANT: always destroy when you're done!

# Destroy without confirmation (for automation)
terraform destroy -auto-approve

# 5. SHOW — see current state of infrastructure
terraform show

# 6. OUTPUT — show output values
terraform output

# 7. FORMAT — auto-format your .tf files
terraform fmt

# 8. VALIDATE — check your .tf files for syntax errors
terraform validate
```

### What is terraform.tfstate?
After `terraform apply`, Terraform saves a file called `terraform.tfstate`.
This file tracks what exists on AWS so Terraform knows what to update or destroy.
**Never delete this file** and **never push it to GitHub** (it contains sensitive info).

### Our complete main.tf explained line by line:

```hcl
# Tell Terraform to use the AWS provider in Paris region
provider "aws" {
  region = "eu-west-3"   # eu-west-3 = Paris, France
}

# Create a firewall (Security Group)
resource "aws_security_group" "satping_sg" {
  name        = "satping-sg"
  description = "Allow SSH"

  # Allow SSH connections IN (port 22)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # from any IP address
  }

  # Allow ALL connections OUT
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create a virtual server (EC2 instance)
resource "aws_instance" "satping" {
  ami           = "ami-0302f42a44bf53a45"  # Amazon Linux 2023 image ID in Paris
  instance_type = "t3.micro"               # smallest/cheapest server (free tier)
  key_name      = "satping-key"            # SSH key pair name for login

  # Attach the firewall we created above
  vpc_security_group_ids = [aws_security_group.satping_sg.id]

  tags = {
    Name = "satping-server"   # name shown in AWS console
  }
}
```

### Terraform workflow for this project:

```bash
cd terraform

terraform init      # first time only

terraform plan      # always check before applying

terraform apply     # create server on AWS
                    # → EC2 instance created
                    # → Security group created
                    # → SSH key attached

# ... do your work ...

terraform destroy   # when done, destroy to avoid charges
```

---

## 📦 AWS ECR — Docker Image Registry

### What is ECR?
ECR = Elastic Container Registry.
It is a private storage for your Docker images on AWS.
Your AWS server pulls the image from ECR when it starts.

### Why not use DockerHub?
ECR is private (only your AWS account can access it) and faster within AWS network.

### Workflow:
```bash
# 1. Create the registry
aws ecr create-repository --repository-name satping --region eu-west-3

# 2. Login Docker to ECR
aws ecr get-login-password --region eu-west-3 | \
  docker login --username AWS --password-stdin \
  439638384547.dkr.ecr.eu-west-3.amazonaws.com

# 3. Build image
docker build -t satping .

# 4. Tag image with ECR address
docker tag satping:latest \
  439638384547.dkr.ecr.eu-west-3.amazonaws.com/satping:latest

# 5. Push image to ECR
docker push \
  439638384547.dkr.ecr.eu-west-3.amazonaws.com/satping:latest
```

---

## 🤖 Ansible — Automated Server Configuration

### What is Ansible?
Ansible is an automation tool that configures servers automatically.
Instead of SSHing into a server and running commands manually one by one,
you write a "playbook" (a list of tasks) and Ansible runs them all automatically.

**Without Ansible:**
```
ssh into server → apt install docker → systemctl start docker → docker pull → docker run
(manual, slow, error-prone, hard to repeat)
```

**With Ansible:**
```
ansible-playbook playbook.yml
(automatic, fast, repeatable, consistent)
```

### Key files:

**inventory.ini** — tells Ansible which servers to configure:
```ini
[satping]                    # group name
35.181.167.37                # server IP address
  ansible_user=ec2-user      # Linux username to login with
  ansible_ssh_private_key_file=~/.ssh/satping-key.pem  # SSH key location
```

**playbook.yml** — the list of tasks to run on the server:
```yaml
---
- name: Configure and run SatPing server
  hosts: satping      # run on servers in the [satping] group
  become: yes         # run as root (sudo)

  tasks:
    - name: Install Docker         # task name (shown during execution)
      dnf:                         # use dnf package manager (Amazon Linux)
        name: docker
        state: present             # "present" means install it

    - name: Start Docker service
      service:
        name: docker
        state: started             # make sure Docker is running
        enabled: yes               # start automatically on server reboot

    - name: Login to ECR
      shell: |                     # run a shell command
        aws ecr get-login-password --region eu-west-3 | \
        docker login --username AWS --password-stdin \
        439638384547.dkr.ecr.eu-west-3.amazonaws.com
      environment:                 # pass environment variables
        AWS_ACCESS_KEY_ID: "{{ aws_access_key }}"      # variable from --extra-vars
        AWS_SECRET_ACCESS_KEY: "{{ aws_secret_key }}"

    - name: Pull and run SatPing
      shell: |
        docker pull 439638384547.dkr.ecr.eu-west-3.amazonaws.com/satping:latest
        docker stop satping || true   # stop if running (|| true = ignore error if not running)
        docker rm satping || true     # remove old container
        docker run -d --name satping \
          -e N2YO_API_KEY={{ n2yo_api_key }} \
          439638384547.dkr.ecr.eu-west-3.amazonaws.com/satping:latest
```

### Ansible commands:

```bash
# Run a playbook
ansible-playbook -i inventory.ini playbook.yml

# Run with extra variables (pass secrets at runtime)
ansible-playbook -i inventory.ini playbook.yml \
  --extra-vars "n2yo_api_key=KEY aws_access_key=KEY aws_secret_key=KEY"

# Test connection to servers (ping)
ansible -i inventory.ini all -m ping

# Run a single command on all servers
ansible -i inventory.ini all -m shell -a "docker ps"

# Run playbook with verbose output (for debugging)
ansible-playbook -i inventory.ini playbook.yml -v
```

### What each Ansible module does:

| Module | What it does |
|--------|--------------|
| `dnf` | Install/remove packages on Amazon Linux (like apt on Ubuntu) |
| `service` | Start/stop/enable Linux services |
| `shell` | Run any shell command |
| `user` | Manage Linux users and groups |
| `copy` | Copy files to the server |
| `file` | Create/delete files and folders |

---

## ☸️ Kubernetes — Container Orchestration

### What is Kubernetes?
Kubernetes manages your containers automatically.
If a container crashes → Kubernetes restarts it automatically.
If you need more → Kubernetes scales up automatically.
If a server dies → Kubernetes moves containers to healthy servers.

### Key concepts:

| Term | Plain English |
|------|---------------|
| **Pod** | One running container (the smallest unit) |
| **Deployment** | Says "I want 2 pods of satping always running" |
| **Secret** | Encrypted storage for passwords and API keys |
| **Node** | A server that runs pods |
| **Cluster** | A group of nodes managed by Kubernetes |

### Our deployment file explained:

```yaml
apiVersion: apps/v1
kind: Deployment          # this is a Deployment resource
metadata:
  name: satping           # name of the deployment
spec:
  replicas: 2             # run 2 copies of the container
  selector:
    matchLabels:
      app: satping        # manage pods with label app=satping
  template:
    metadata:
      labels:
        app: satping      # give this label to pods
    spec:
      containers:
      - name: satping
        image: 439638384547.dkr.ecr.eu-west-3.amazonaws.com/satping:latest
        env:
        - name: N2YO_API_KEY
          valueFrom:
            secretKeyRef:         # read from Kubernetes Secret
              name: satping-secrets
              key: n2yo-api-key
        resources:
          requests:               # minimum resources guaranteed
            memory: "64Mi"        # 64 megabytes RAM
            cpu: "250m"           # 0.25 CPU cores
          limits:                 # maximum resources allowed
            memory: "128Mi"       # 128 megabytes RAM
            cpu: "500m"           # 0.5 CPU cores
```

### Kubernetes commands:

```bash
# Apply a configuration file
kubectl apply -f deployment.yml

# See running pods
kubectl get pods

# See deployments
kubectl get deployments

# See logs of a pod
kubectl logs pod-name
kubectl logs -f pod-name   # follow live

# Delete a deployment
kubectl delete -f deployment.yml

# Describe a pod (detailed info + events)
kubectl describe pod pod-name

# Scale a deployment
kubectl scale deployment satping --replicas=3
```

---

## 📊 Prometheus — Metrics Collection

### What is Prometheus?
Prometheus is a monitoring tool that regularly visits your app
and collects numbers (metrics) like "how many satellites are above Paris right now".
It stores these numbers over time so you can see trends.

### How it works:
```
Every 15 seconds:
Prometheus → visits http://satping:8000 → reads metrics → stores them
```

### Our prometheus.yml config:
```yaml
global:
  scrape_interval: 15s      # collect metrics every 15 seconds

scrape_configs:
  - job_name: 'satping'     # name for this collection job
    static_configs:
      - targets: ['satping:8000']   # where to collect metrics from
```

### What metric did we expose?
In our Python app we added:
```python
from prometheus_client import start_http_server, Gauge

# Create a metric called "satellites_above_paris"
satellites_above = Gauge('satellites_above_paris', 'Number of satellites above Paris')

# Update it every time we call the API
satellites_above.set(count)

# Start the metrics server on port 8000
start_http_server(8000)
```

Visit http://localhost:9090 → Status → Targets to see if Prometheus is collecting your metrics.
Query `satellites_above_paris` to see the current value.

---

## 📈 Grafana — Metrics Visualization

### What is Grafana?
Grafana reads data from Prometheus and displays it as beautiful dashboards and graphs.
Prometheus collects the data. Grafana shows it visually.

### Setup steps:
1. Go to http://localhost:3000
2. Login: admin / admin
3. Add Prometheus as data source → URL: http://prometheus:9090
4. Create dashboard → Add panel → Query: `satellites_above_paris`
5. Choose visualization type (Stat for big number, Graph for timeline)

---

## 🔑 SSH — Remote Server Login

### What is SSH?
SSH (Secure Shell) lets you log into a remote Linux server securely from your terminal.
Like opening a terminal window but on a server that's physically in Paris.

```bash
# Connect to server using SSH key
ssh -i ~/.ssh/satping-key.pem ec2-user@35.181.167.37
# -i = identity file (your private key)
# ec2-user = default username on Amazon Linux
# 35.181.167.37 = server's public IP address

# Once connected you see:
[ec2-user@ip-172-31-9-202 ~]$   # you are now ON the server

# Check running containers on the server
docker ps

# See app logs
docker logs satping

# Exit the server
exit
```

---

## 🗺️ Full Project Flow — Start to Finish

```
1. Write Python code on Windows
          ↓
2. git push → GitHub
          ↓
3. GitHub Actions automatically:
   - installs Python
   - builds Docker image
   - runs tests
   - shows ✅ or ❌
          ↓
4. Build Docker image locally
   docker build -t satping .
          ↓
5. Push image to AWS ECR
   docker push ...ecr.../satping:latest
          ↓
6. Terraform creates AWS server
   terraform apply
   → EC2 instance in Paris
   → Security group (firewall)
          ↓
7. Ansible configures the server automatically
   ansible-playbook playbook.yml
   → installs Docker on server
   → logs into ECR
   → pulls the Docker image
   → starts the container
          ↓
8. App runs 24/7 on AWS
   tracking satellites every 60 seconds
          ↓
9. Prometheus collects metrics every 15s
   http://server:8000
          ↓
10. Grafana displays live dashboard
    http://localhost:3000
```

---

## 💰 AWS Cost Management

```bash
# Always destroy when not using to avoid charges
cd terraform
terraform destroy

# Recreate anytime with
terraform apply
```

**t3.micro free tier:** 750 hours/month free for 12 months on a new AWS account.
Always destroy when finished working to stay within free tier.
