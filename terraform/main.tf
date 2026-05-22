provider "aws" {
  region = "eu-west-3"
}

resource "aws_security_group" "satping_sg" {
  name        = "satping-sg"
  description = "Allow SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "satping" {
  ami                    = "ami-0302f42a44bf53a45"
  instance_type          = "t3.micro"
  key_name               = "satping-key"
  vpc_security_group_ids = [aws_security_group.satping_sg.id]

  tags = {
    Name = "satping-server"
  }
}