# ── networking.tf — VPC, Subnets, Security Groups ───────────
# VPC = Virtual Private Cloud = mạng riêng của bạn trên AWS
# Giống như bạn thuê 1 khu đất riêng, tự thiết kế đường đi

# ── VPC: Mạng riêng ─────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"   # 65,536 địa chỉ IP
  enable_dns_hostnames = true             # EC2 có hostname dạng ip-10-0-x-x
  enable_dns_support   = true

  tags = merge(local.common_tags, { Name = "${local.prefix}-vpc" })
}

# ── Internet Gateway: Cổng kết nối internet ─────────────────
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.common_tags, { Name = "${local.prefix}-igw" })
}

# ── Public Subnet: Cho Nginx/Load Balancer ──────────────────
# Public = có thể access từ internet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"   # 256 địa chỉ IP
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true             # EC2 tự có public IP

  tags = merge(local.common_tags, { Name = "${local.prefix}-subnet-public" })
}

# ── Private Subnet: Cho App + DB ────────────────────────────
# Private = KHÔNG access được từ internet trực tiếp
# App và DB phải nằm đây — bảo mật hơn
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}a"

  tags = merge(local.common_tags, { Name = "${local.prefix}-subnet-private" })
}

# ── Route Table: Bảng định tuyến ────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  # Traffic ra internet → qua Internet Gateway
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-rt-public" })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ── Security Group: Firewall rules ──────────────────────────

# SG cho Nginx — chỉ cho vào port 80 và 443
resource "aws_security_group" "nginx" {
  name        = "${local.prefix}-sg-nginx"
  description = "Security group cho Nginx reverse proxy"
  vpc_id      = aws_vpc.main.id

  # Inbound: cho phép HTTP và HTTPS từ internet
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # từ mọi nơi
    description = "HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # Outbound: cho phép ra ngoài thoải mái
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"   # tất cả protocols
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-sg-nginx" })
}

# SG cho App — chỉ cho Nginx vào port 8000
resource "aws_security_group" "app" {
  name        = "${local.prefix}-sg-app"
  description = "Security group cho FastAPI app"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.nginx.id]   # chỉ từ Nginx!
    description     = "FastAPI tu Nginx"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-sg-app" })
}

# SG cho DB — chỉ cho App vào port 5432
resource "aws_security_group" "db" {
  name        = "${local.prefix}-sg-db"
  description = "Security group cho PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]   # chỉ từ App!
    description     = "PostgreSQL tu App"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.prefix}-sg-db" })
}
