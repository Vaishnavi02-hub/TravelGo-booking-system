#!/bin/bash

# TravelGo EC2 Deployment Script
# This script automates the deployment of TravelGo on Ubuntu EC2

set -e  # Exit on error

echo "=========================================="
echo "TravelGo EC2 Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Step 1: Update system
echo ""
print_info "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Step 2: Install dependencies
echo ""
print_info "Step 2: Installing Python, pip, git, and nginx..."
sudo apt install -y python3 python3-pip python3-venv git nginx
print_success "Dependencies installed"

# Step 3: Install AWS CLI
echo ""
print_info "Step 3: Installing AWS CLI..."
if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    sudo apt install -y unzip
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    print_success "AWS CLI installed"
else
    print_success "AWS CLI already installed"
fi

# Step 4: Get repository
echo ""
print_info "Step 4: Getting TravelGo application..."
read -p "Enter Git repository URL (or press Enter to skip): " REPO_URL

if [ -n "$REPO_URL" ]; then
    git clone "$REPO_URL" travelgo
    cd travelgo/travelgo_project
    print_success "Repository cloned"
else
    print_info "Skipping git clone. Make sure to upload files manually."
    if [ -d "travelgo_project" ]; then
        cd travelgo_project
    else
        print_error "travelgo_project directory not found"
        exit 1
    fi
fi

# Step 5: Create virtual environment
echo ""
print_info "Step 5: Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
print_success "Virtual environment created"

# Step 6: Install Python packages
echo ""
print_info "Step 6: Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python packages installed"

# Step 7: Configure environment
echo ""
print_info "Step 7: Configuring environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    print_info "Created .env file from template"
    
    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/your-super-secret-key-change-in-production/$SECRET_KEY/g" .env
    
    print_info "Please configure AWS settings in .env file:"
    echo "  - USE_AWS=true"
    echo "  - AWS_REGION=us-east-1"
    echo "  - SNS_TOPIC_ARN=<your-sns-topic-arn>"
    
    read -p "Do you want to edit .env now? (y/n): " EDIT_ENV
    if [ "$EDIT_ENV" = "y" ]; then
        nano .env
    fi
else
    print_success ".env file already exists"
fi

# Step 8: Configure AWS credentials
echo ""
print_info "Step 8: AWS Configuration..."
print_info "Choose AWS authentication method:"
echo "  1. AWS Configure (enter credentials)"
echo "  2. IAM Role (recommended for EC2)"
echo "  3. Skip (configure later)"
read -p "Enter choice (1-3): " AWS_CHOICE

case $AWS_CHOICE in
    1)
        aws configure
        print_success "AWS credentials configured"
        ;;
    2)
        print_info "Make sure IAM role is attached to this EC2 instance"
        print_info "The role should have DynamoDB and SNS permissions"
        ;;
    3)
        print_info "AWS configuration skipped"
        ;;
esac

# Step 9: Create systemd service
echo ""
print_info "Step 9: Creating systemd service..."
WORKING_DIR=$(pwd)
SERVICE_FILE="/etc/systemd/system/travelgo.service"

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=TravelGo Flask Application
After=network.target

[Service]
User=$USER
WorkingDirectory=$WORKING_DIR
Environment="PATH=$WORKING_DIR/venv/bin"
ExecStart=$WORKING_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable travelgo
print_success "Systemd service created"

# Step 10: Configure Nginx
echo ""
print_info "Step 10: Configuring Nginx..."
read -p "Configure Nginx reverse proxy? (y/n): " CONFIGURE_NGINX

if [ "$CONFIGURE_NGINX" = "y" ]; then
    NGINX_CONF="/etc/nginx/sites-available/travelgo"
    
    sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $WORKING_DIR/static;
        expires 30d;
    }
}
EOF

    sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl restart nginx
    print_success "Nginx configured"
else
    print_info "Nginx configuration skipped"
fi

# Step 11: Start application
echo ""
print_info "Step 11: Starting TravelGo application..."
sudo systemctl start travelgo
sleep 3
sudo systemctl status travelgo --no-pager

if sudo systemctl is-active --quiet travelgo; then
    print_success "TravelGo application started successfully!"
else
    print_error "Failed to start application. Check logs with: sudo journalctl -u travelgo -f"
    exit 1
fi

# Final summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
print_success "TravelGo is now running!"
echo ""
echo "Access your application at:"
if [ "$CONFIGURE_NGINX" = "y" ]; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo "  http://$PUBLIC_IP"
else
    echo "  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
fi
echo ""
echo "Useful commands:"
echo "  sudo systemctl status travelgo   # Check status"
echo "  sudo systemctl restart travelgo  # Restart app"
echo "  sudo journalctl -u travelgo -f   # View logs"
echo ""
echo "Don't forget to:"
echo "  1. Configure AWS settings in .env"
echo "  2. Setup DynamoDB tables"
echo "  3. Create SNS topic"
echo "  4. Confirm SNS email subscription"
echo "=========================================="
