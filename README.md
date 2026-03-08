# 🚀 TravelGo - Full-Stack Travel Booking Application

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![AWS](https://img.shields.io/badge/AWS-DynamoDB%20%7C%20SNS-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A complete, production-ready travel booking web application built with Python Flask and integrated with AWS services. Book buses, trains, flights, and hotels all in one place!

## 📋 Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [AWS Setup](#aws-setup)
- [Running the Application](#running-the-application)
- [Deployment](#deployment)
- [API Routes](#api-routes)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### User Management
- ✅ User registration with secure password hashing (Werkzeug)
- ✅ User authentication and login
- ✅ Session-based authentication
- ✅ Secure logout functionality

### Booking System
- 🚌 **Bus Booking** - Select seats and book comfortable bus journeys
- 🚆 **Train Booking** - Choose from Economy, Business, and First Class
- ✈️ **Flight Booking** - Book flights across multiple airlines
- 🏨 **Hotel Booking** - Filter by budget or luxury categories

### Cloud Integration
- ☁️ AWS DynamoDB for scalable data storage
- 📧 AWS SNS for email notifications
- 🔄 Automatic fallback to in-memory storage when AWS is not configured
- 🔐 Secure AWS credential handling

### Additional Features
- 📊 Booking history and management
- 🆔 Unique booking ID generation (UUID)
- 📱 Responsive design for mobile and desktop
- 🎨 Modern, clean UI with card-based design
- ⚡ Flash messages for user feedback
- 🚫 Booking cancellation with email notifications

## 🛠️ Technologies Used

### Backend
- **Python 3.9+** - Programming language
- **Flask 3.0.0** - Web framework
- **Werkzeug** - Password hashing and security
- **boto3** - AWS SDK for Python
- **python-dotenv** - Environment variable management
- **Gunicorn** - Production WSGI server

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling with modern design
- **Jinja2** - Template engine
- **JavaScript** - Client-side interactivity

### Cloud Services
- **AWS DynamoDB** - NoSQL database
- **AWS SNS** - Email notification service
- **AWS EC2** - Deployment (optional)

## 📁 Project Structure

```
travelgo_project/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── home.html             # Landing page
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # User dashboard
│   ├── booking.html          # Dynamic booking page
│   └── history.html          # Booking history page
│
└── static/                    # Static files
    └── css/
        └── style.css         # Main stylesheet
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9 or higher**
- **pip** (Python package installer)
- **Git** (for version control)
- **AWS Account** (optional, for cloud features)
- **AWS CLI** (optional, for AWS configuration)

## 💻 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/travelgo.git
cd travelgo_project
```

### 2. Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# On Windows: notepad .env
# On macOS/Linux: nano .env
```

## ⚙️ Configuration

### Environment Variables

Edit the `.env` file with your configuration:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-in-production

# AWS Configuration
USE_AWS=false                    # Set to 'true' to enable AWS
AWS_REGION=us-east-1
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:TravelGo-Notifications

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000
```

### Generate a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## ☁️ AWS Setup

### Step 1: Create DynamoDB Tables

#### Users Table
```bash
aws dynamodb create-table \
    --table-name TravelGo_Users \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --key-schema AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

#### Bookings Table
```bash
aws dynamodb create-table \
    --table-name TravelGo_Bookings \
    --attribute-definitions AttributeName=booking_id,AttributeType=S \
    --key-schema AttributeName=booking_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

### Step 2: Create SNS Topic

```bash
# Create SNS topic
aws sns create-topic --name TravelGo-Notifications --region us-east-1

# Subscribe your email
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:TravelGo-Notifications \
    --protocol email \
    --notification-endpoint your-email@example.com
```

### Step 3: Configure AWS Credentials

**Option 1: AWS CLI Configuration (Recommended)**
```bash
aws configure
```

**Option 2: Environment Variables**
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

**Option 3: IAM Role (For EC2 deployment)**
- Attach appropriate IAM role to your EC2 instance

### Step 4: Set IAM Permissions

Ensure your AWS user/role has the following permissions:

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
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:us-east-1:*:TravelGo-Notifications"
        }
    ]
}
```

## 🚀 Running the Application

### Development Mode

```bash
# Activate virtual environment first
python app.py
```

The application will be available at: `http://localhost:5000`

### Production Mode with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Options explained:
- `-w 4`: Run with 4 worker processes
- `-b 0.0.0.0:5000`: Bind to all interfaces on port 5000
- `app:app`: Module name and Flask app instance

## 🌐 Deployment

### Deploying on AWS EC2

#### 1. Launch EC2 Instance

- Choose **Ubuntu 22.04 LTS** or **Amazon Linux 2**
- Instance type: **t2.micro** (free tier eligible) or higher
- Configure security group to allow:
  - SSH (port 22)
  - HTTP (port 80)
  - Custom TCP (port 5000)

#### 2. Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Git
sudo apt install git -y
```

#### 4. Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/yourusername/travelgo.git
cd travelgo_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create and configure .env file
cp .env.example .env
nano .env
```

#### 5. Configure AWS Credentials on EC2

```bash
aws configure
```

Or attach an IAM role to the EC2 instance.

#### 6. Run Application

**Option A: Direct Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Option B: Systemd Service (Recommended)**

Create service file:
```bash
sudo nano /etc/systemd/system/travelgo.service
```

Add content:
```ini
[Unit]
Description=TravelGo Flask Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/travelgo_project
Environment="PATH=/home/ubuntu/travelgo_project/venv/bin"
ExecStart=/home/ubuntu/travelgo_project/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable travelgo
sudo systemctl start travelgo
sudo systemctl status travelgo
```

#### 7. Configure Nginx (Optional but Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/travelgo
```

Add configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /home/ubuntu/travelgo_project/static;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/travelgo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔗 API Routes

| Route | Method | Description | Authentication |
|-------|--------|-------------|----------------|
| `/` | GET | Home page | No |
| `/register` | GET, POST | User registration | No |
| `/login` | GET, POST | User login | No |
| `/logout` | GET | User logout | Yes |
| `/dashboard` | GET | User dashboard | Yes |
| `/book/bus` | GET | Bus booking page | Yes |
| `/book/train` | GET | Train booking page | Yes |
| `/book/flight` | GET | Flight booking page | Yes |
| `/book/hotel` | GET | Hotel booking page | Yes |
| `/confirm-booking` | POST | Process booking | Yes |
| `/history` | GET | View booking history | Yes |
| `/cancel-booking/<id>` | POST | Cancel booking | Yes |

## 📸 Screenshots

### Home Page
Beautiful landing page with travel options and features.

### Dashboard
User dashboard with quick access to all booking options.

### Booking Pages
Dynamic booking pages for buses, trains, flights, and hotels.

### Booking History
View and manage all your bookings in one place.

## 🧪 Testing

### Manual Testing

1. **User Registration**
   - Navigate to `/register`
   - Create a new account
   - Verify password validation

2. **User Login**
   - Navigate to `/login`
   - Login with created credentials
   - Verify session creation

3. **Booking Flow**
   - Go to dashboard
   - Select booking type
   - Complete booking
   - Verify booking ID generation
   - Check email notification (if AWS configured)

4. **Booking History**
   - View all bookings
   - Test cancellation
   - Verify cancellation notification

### Local Development (Without AWS)

Set `USE_AWS=false` in `.env` to test with in-memory storage.

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Use strong secret keys** - Generate using `secrets` module
3. **Rotate AWS credentials regularly**
4. **Use IAM roles** instead of hardcoded credentials on EC2
5. **Enable HTTPS** in production (use Let's Encrypt)
6. **Keep dependencies updated** - Run `pip list --outdated`
7. **Use environment-specific configurations**

## 🐛 Troubleshooting

### AWS Connection Issues

```bash
# Check AWS credentials
aws sts get-caller-identity

# Test DynamoDB access
aws dynamodb list-tables

# Test SNS access
aws sns list-topics
```

### Application Won't Start

```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for port conflicts
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows
```

### Database Errors

- Verify DynamoDB table names match configuration
- Check IAM permissions
- Ensure AWS region is correct

## 📝 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Flask framework and community
- AWS for cloud services
- All contributors and users of TravelGo

## 📧 Contact

For questions or support, please contact:
- Email: support@travelgo.com
- GitHub Issues: [Create an issue](https://github.com/yourusername/travelgo/issues)

---

**Made with ❤️ by TravelGo Team**

⭐ Star this repository if you find it helpful!
