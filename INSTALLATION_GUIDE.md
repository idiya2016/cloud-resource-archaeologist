# Cloud Archaeologist - Installation Guide

## Prerequisites

Before installing Cloud Archaeologist, ensure you have the following:

- Python 3.8 or higher
- pip package manager
- AWS CLI installed and configured (optional but recommended)
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cloud-archaeologist.git
cd cloud-archaeologist
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS Credentials

You have several options to configure AWS credentials:

#### Option A: AWS CLI Configuration (Recommended)
```bash
aws configure
```

#### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=your_region
```

#### Option C: AWS Credentials File
Edit `~/.aws/credentials`:
```
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
```

And `~/.aws/config`:
```
[default]
region = your_region
```

## Verify Installation

Run a basic scan to verify everything is working:

```bash
python cloud_archaeologist.py --format txt
```

## Troubleshooting Installation Issues

### Common Issues and Solutions:

1. **Permission Errors**: Run with `--user` flag or use virtual environment
2. **Missing Dependencies**: Ensure all requirements are installed via pip
3. **AWS Authentication**: Verify your AWS credentials are properly configured
4. **Python Version**: Ensure you're using Python 3.8 or higher

## Next Steps

After successful installation, check out our:
- [API_REFERENCE.md](API_REFERENCE.md) for detailed usage
- [AWS_IAM_POLICY.json](AWS_IAM_POLICY.json) for required permissions
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues