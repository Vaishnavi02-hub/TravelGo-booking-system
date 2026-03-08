# EC2 Deployment Guide for TravelGo

## Prerequisites
- AWS Account
- AWS CLI installed and configured
- EC2 Key Pair created

## Step 1: Launch EC2 Instance

### Option A: Using AWS Console

1. Go to EC2 Dashboard → Launch Instance
2. **Configuration:**
   - **Name:** TravelGo-Server
   - **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance Type:** t2.micro (or t2.small for better performance)
   - **Key pair:** Select or create a new key pair
   - **Network settings:**
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow Custom TCP (port 5000) from anywhere
   - **Storage:** 8-16 GB (default is fine)
3. Click **Launch Instance**

### Option B: Using AWS CLI

```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --key-name your-key-pair-name \
    --security-group-ids sg-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=TravelGo-Server}]'
```

## Step 2: Configure Security Group

Ensure your security group allows:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | Your IP (or 0.0.0.0/0) |
| HTTP | TCP | 80 | 0.0.0.0/0 |
| HTTPS | TCP | 443 | 0.0.0.0/0 |
| Custom TCP | TCP | 5000 | 0.0.0.0/0 |

## Step 3: Connect to EC2 Instance

```bash
# Get your EC2 instance public IP from AWS Console
ssh -i "your-key.pem" ubuntu@<EC2-PUBLIC-IP>
```

**Windows users:** Use PuTTY or Windows Terminal with WSL

## Step 4: Install Dependencies on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Git
sudo apt install git -y

# Install Nginx (optional but recommended)
sudo apt install nginx -y
```

## Step 5: Setup Application

```bash
# Clone your repository (replace with your repo URL)
git clone https://github.com/yourusername/travelgo.git
cd travelgo/travelgo_project

# Or upload files using SCP
# scp -i "your-key.pem" -r travelgo_project ubuntu@<EC2-IP>:~/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 6: Configure AWS Credentials on EC2

### Option A: AWS Configure (Recommended for testing)

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Option B: IAM Role (Recommended for production)

1. Create IAM role with these policies:
   - DynamoDB: PutItem, GetItem, Scan, DeleteItem
   - SNS: Publish

2. Attach role to EC2 instance:
   - EC2 Console → Actions → Security → Modify IAM role
   - Select the created role

**IAM Policy Example:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Scan",
                "dynamodb:DeleteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:*:table/TravelGo_Users",
                "arn:aws:dynamodb:us-east-1:*:table/TravelGo_Bookings"
            ]
        },
        {
            "Effect": "Allow",
            "Action": ["sns:Publish"],
            "Resource": "arn:aws:sns:us-east-1:*:TravelGo-Notifications"
        }
    ]
}
```

## Step 7: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env
```

**Set these values:**
```env
SECRET_KEY=<generate-a-secure-key>
USE_AWS=true
AWS_REGION=us-east-1
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:TravelGo-Notifications
FLASK_ENV=production
FLASK_DEBUG=false
```

**Generate secure key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Step 8: Run Application

### Method 1: Direct Gunicorn (For Testing)

```bash
# Activate virtual environment
source venv/bin/activate

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Test from your browser
# http://<EC2-PUBLIC-IP>:5000
```

### Method 2: Systemd Service (Recommended for Production)

```bash
# Create service file
sudo nano /etc/systemd/system/travelgo.service
```

**Add this content:**
```ini
[Unit]
Description=TravelGo Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/travelgo/travelgo_project
Environment="PATH=/home/ubuntu/travelgo/travelgo_project/venv/bin"
ExecStart=/home/ubuntu/travelgo/travelgo_project/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable travelgo
sudo systemctl start travelgo
sudo systemctl status travelgo
```

**Service commands:**
```bash
sudo systemctl start travelgo    # Start service
sudo systemctl stop travelgo     # Stop service
sudo systemctl restart travelgo  # Restart service
sudo systemctl status travelgo   # Check status
sudo journalctl -u travelgo -f   # View logs
```

## Step 9: Configure Nginx Reverse Proxy (Optional but Recommended)

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/travelgo
```

**Add configuration:**
```nginx
server {
    listen 80;
    server_name <EC2-PUBLIC-IP> your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/ubuntu/travelgo/travelgo_project/static;
        expires 30d;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/travelgo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Now access your app at:** `http://<EC2-PUBLIC-IP>`

## Step 10: Setup SSL with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Updating Your Application

```bash
# Navigate to project directory
cd ~/travelgo/travelgo_project

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl restart travelgo
```

## Monitoring and Logs

### View Application Logs
```bash
# Real-time logs
sudo journalctl -u travelgo -f

# Last 100 lines
sudo journalctl -u travelgo -n 100

# Logs from today
sudo journalctl -u travelgo --since today
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Service Status
```bash
sudo systemctl status travelgo
sudo systemctl status nginx
```

## Troubleshooting

### Application won't start
```bash
# Check Python path
which python3

# Test app manually
source venv/bin/activate
python3 app.py

# Check permissions
ls -la /home/ubuntu/travelgo/travelgo_project
```

### Port 5000 already in use
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

### AWS Connection Issues
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM role (if using)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Test DynamoDB access
aws dynamodb list-tables --region us-east-1
```

## Cost Optimization

- **Use t2.micro** for free tier (first 12 months)
- **Stop instance** when not needed
- **Use DynamoDB on-demand** billing
- **Monitor CloudWatch** for usage
- **Set up billing alerts**

## Security Best Practices

1. **Never commit .env** to GitHub
2. **Use IAM roles** instead of access keys
3. **Restrict security group** to specific IPs when possible
4. **Keep system updated:** `sudo apt update && sudo apt upgrade`
5. **Enable CloudWatch logs**
6. **Use HTTPS** in production
7. **Regular backups** of DynamoDB tables

## Backup Strategy

### Manual DynamoDB Backup
```bash
aws dynamodb create-backup \
    --table-name TravelGo_Users \
    --backup-name TravelGo_Users_Backup_$(date +%Y%m%d)

aws dynamodb create-backup \
    --table-name TravelGo_Bookings \
    --backup-name TravelGo_Bookings_Backup_$(date +%Y%m%d)
```

### Enable Point-in-Time Recovery
```bash
aws dynamodb update-continuous-backups \
    --table-name TravelGo_Users \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

## Auto-scaling (Optional)

For high traffic, configure Application Load Balancer and Auto Scaling Group:
- Min instances: 2
- Max instances: 5
- Target CPU: 70%

Refer to AWS documentation for detailed setup.

---

**Your TravelGo application is now deployed on AWS EC2!** 🚀

Access it at: `http://<EC2-PUBLIC-IP>` or `https://your-domain.com`
