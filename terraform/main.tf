provider "aws" {
  region = "eu-west-3"
}

# Creates a virtual server on AWS
resource "aws_instance" "satping" {
  ami           = "ami-0302f42a44bf53a45"  # Amazon Linux 2 in Paris
  instance_type = "t3.micro"               # free tier in eu-west-3

  tags = {
    Name = "satping-server"
  }
}