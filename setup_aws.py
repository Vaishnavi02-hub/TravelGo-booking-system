"""
AWS Setup Script for TravelGo
This script creates the required DynamoDB tables and SNS topic
"""

import boto3
from botocore.exceptions import ClientError
import sys

# AWS Configuration
AWS_REGION = 'us-east-1'  # Change this to your preferred region

def create_dynamodb_tables():
    """Create DynamoDB tables for TravelGo"""
    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
    
    print("=" * 60)
    print("Creating DynamoDB Tables...")
    print("=" * 60)
    
    # Create Users Table
    try:
        print("\n1. Creating TravelGo_Users table...")
        dynamodb.create_table(
            TableName='TravelGo_Users',
            KeySchema=[
                {'AttributeName': 'email', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'email', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Application', 'Value': 'TravelGo'},
                {'Key': 'Environment', 'Value': 'Production'}
            ]
        )
        print("✓ TravelGo_Users table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ TravelGo_Users table already exists")
        else:
            print(f"✗ Error creating Users table: {e}")
            return False
    
    # Create Bookings Table
    try:
        print("\n2. Creating TravelGo_Bookings table...")
        dynamodb.create_table(
            TableName='TravelGo_Bookings',
            KeySchema=[
                {'AttributeName': 'booking_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'booking_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {'Key': 'Application', 'Value': 'TravelGo'},
                {'Key': 'Environment', 'Value': 'Production'}
            ]
        )
        print("✓ TravelGo_Bookings table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("✓ TravelGo_Bookings table already exists")
        else:
            print(f"✗ Error creating Bookings table: {e}")
            return False
    
    # Wait for tables to be active
    print("\n3. Waiting for tables to become active...")
    waiter = dynamodb.get_waiter('table_exists')
    
    try:
        waiter.wait(TableName='TravelGo_Users')
        waiter.wait(TableName='TravelGo_Bookings')
        print("✓ All tables are active and ready")
    except Exception as e:
        print(f"✗ Error waiting for tables: {e}")
        return False
    
    return True


def create_sns_topic():
    """Create SNS topic for email notifications"""
    sns = boto3.client('sns', region_name=AWS_REGION)
    
    print("\n" + "=" * 60)
    print("Creating SNS Topic...")
    print("=" * 60)
    
    try:
        print("\n1. Creating TravelGo-Notifications topic...")
        response = sns.create_topic(
            Name='TravelGo-Notifications',
            Tags=[
                {'Key': 'Application', 'Value': 'TravelGo'},
                {'Key': 'Environment', 'Value': 'Production'}
            ]
        )
        topic_arn = response['TopicArn']
        print(f"✓ SNS Topic created successfully")
        print(f"   Topic ARN: {topic_arn}")
        
        # Prompt for email subscription
        print("\n2. Email subscription...")
        email = input("   Enter your email address for notifications (or press Enter to skip): ").strip()
        
        if email:
            sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            print(f"✓ Subscription request sent to {email}")
            print("   IMPORTANT: Check your email and confirm the subscription!")
        else:
            print("   Skipped email subscription")
        
        return topic_arn
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'TopicAlreadyExists':
            # Get existing topic ARN
            response = sns.create_topic(Name='TravelGo-Notifications')
            topic_arn = response['TopicArn']
            print(f"✓ SNS Topic already exists")
            print(f"   Topic ARN: {topic_arn}")
            return topic_arn
        else:
            print(f"✗ Error creating SNS topic: {e}")
            return None


def verify_aws_credentials():
    """Verify AWS credentials are configured"""
    print("\n" + "=" * 60)
    print("Verifying AWS Credentials...")
    print("=" * 60)
    
    try:
        sts = boto3.client('sts')
        response = sts.get_caller_identity()
        print(f"\n✓ AWS Credentials verified")
        print(f"   Account ID: {response['Account']}")
        print(f"   User ARN: {response['Arn']}")
        print(f"   Region: {AWS_REGION}")
        return True
    except Exception as e:
        print(f"\n✗ AWS Credentials not configured properly")
        print(f"   Error: {e}")
        print("\nPlease configure AWS credentials using one of these methods:")
        print("   1. Run: aws configure")
        print("   2. Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("   3. Use IAM role (for EC2 instances)")
        return False


def update_env_file(topic_arn):
    """Update .env file with AWS configuration"""
    print("\n" + "=" * 60)
    print("Updating .env file...")
    print("=" * 60)
    
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        updated = False
        with open('.env', 'w') as f:
            for line in lines:
                if line.startswith('USE_AWS='):
                    f.write('USE_AWS=true\n')
                    updated = True
                elif line.startswith('AWS_REGION='):
                    f.write(f'AWS_REGION={AWS_REGION}\n')
                elif line.startswith('SNS_TOPIC_ARN=') and topic_arn:
                    f.write(f'SNS_TOPIC_ARN={topic_arn}\n')
                else:
                    f.write(line)
        
        if updated:
            print("✓ .env file updated with AWS configuration")
        else:
            print("✗ Could not update .env file")
            
    except FileNotFoundError:
        print("✗ .env file not found")
        print("   Please copy .env.example to .env first")
    except Exception as e:
        print(f"✗ Error updating .env file: {e}")


def main():
    """Main setup function"""
    print("\n" + "=" * 60)
    print("TravelGo AWS Setup Script")
    print("=" * 60)
    
    # Verify AWS credentials
    if not verify_aws_credentials():
        print("\n✗ Setup failed: AWS credentials not configured")
        sys.exit(1)
    
    # Create DynamoDB tables
    if not create_dynamodb_tables():
        print("\n✗ Setup failed: Could not create DynamoDB tables")
        sys.exit(1)
    
    # Create SNS topic
    topic_arn = create_sns_topic()
    
    # Update .env file
    update_env_file(topic_arn)
    
    # Summary
    print("\n" + "=" * 60)
    print("AWS Setup Complete!")
    print("=" * 60)
    print("\nResources created:")
    print("  ✓ DynamoDB Table: TravelGo_Users")
    print("  ✓ DynamoDB Table: TravelGo_Bookings")
    print("  ✓ SNS Topic: TravelGo-Notifications")
    if topic_arn:
        print(f"\nSNS Topic ARN: {topic_arn}")
    
    print("\nNext steps:")
    print("  1. Confirm your email subscription (check your inbox)")
    print("  2. Restart your Flask application")
    print("  3. Test the application with AWS integration enabled")
    print("\nFor EC2 deployment, refer to the README.md file")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
