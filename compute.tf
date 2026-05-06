# compute.tf

# EC2 cho Nginx — public subnet
resource "aws_instance" "nginx" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.nginx.id]

  tags = merge(local.common_tags, { Name = "${local.prefix}-ec2-nginx" })
}

# EC2 cho App — private subnet  
resource "aws_instance" "app" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.private.id
  vpc_security_group_ids = [aws_security_group.app.id]

  tags = merge(local.common_tags, { Name = "${local.prefix}-ec2-app" })
}