# Quick AWS Setup Commands for TravelGo

## Step 1: Configure AWS CLI

```bash
# Install AWS CLI (if not installed)
# Windows: https://aws.amazon.com/cli/
# Linux: sudo apt install awscli
# Mac: brew install awscli

# Configure credentials
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: us-east-1
# Default output format: json
```

## Step 2: Create DynamoDB Tables

```bash
# Create Users Table
aws dynamodb create-table \
    --table-name TravelGo_Users \
    --attribute-definitions AttributeName=email,AttributeType=S \
    --key-schema AttributeName=email,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Create Bookings Table
aws dynamodb create-table \
    --table-name TravelGo_Bookings \
    --attribute-definitions AttributeName=booking_id,AttributeType=S \
    --key-schema AttributeName=booking_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

# Verify tables
aws dynamodb list-tables --region us-east-1
```

## Step 3: Create SNS Topic

```bash
# Create topic
aws sns create-topic \
    --name TravelGo-Notifications \
    --region us-east-1

# Subscribe your email (replace with your email)
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:TravelGo-Notifications \
    --protocol email \
    --notification-endpoint your-email@example.com \
    --region us-east-1

# Confirm subscription in your email!
```

## Step 4: Get SNS Topic ARN

```bash
# List topics and get ARN
aws sns list-topics --region us-east-1
```

## Step 5: Update .env File

Copy the SNS Topic ARN and update your .env:

```env
USE_AWS=true
AWS_REGION=us-east-1
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:TravelGo-Notifications
```

## Useful Commands

```bash
# Check AWS identity
aws sts get-caller-identity

# Describe Users table
aws dynamodb describe-table --table-name TravelGo_Users --region us-east-1

# Describe Bookings table
aws dynamodb describe-table --table-name TravelGo_Bookings --region us-east-1

# List SNS subscriptions
aws sns list-subscriptions --region us-east-1

# Delete tables (if needed)
aws dynamodb delete-table --table-name TravelGo_Users --region us-east-1
aws dynamodb delete-table --table-name TravelGo_Bookings --region us-east-1

# Delete SNS topic (if needed)
aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT-ID:TravelGo-Notifications
```
