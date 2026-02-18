# Cloud Resource Archaeologist

A comprehensive AWS resource discovery and cost analysis tool that scans for EC2, EBS, S3, EIP, and snapshots with detailed cost calculations and professional reporting.

## Features

- **EC2 Instance Discovery**: Finds all EC2 instances across all AWS regions with cost calculations
- **EBS Volume Discovery**: Identifies all EBS volumes with associated costs
- **S3 Bucket Analysis**: Discovers S3 buckets and estimates storage costs
- **Elastic IP Tracking**: Finds unassociated EIPs that incur charges
- **Snapshot Analysis**: Identifies EBS snapshots with cost implications
- **Professional Reporting**: Generates comprehensive reports with cost summaries and recommendations
- **Cost Calculations**: Provides monthly cost estimates for all resources

## Requirements

- Python 3.7+
- AWS credentials with appropriate permissions

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration

The script uses AWS credentials configured in the following ways:
1. Environment variables (as configured in the script)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM roles (when running on EC2)

## Usage

```bash
# Run a full scan with default settings
python cloud_archaeologist.py

# Use a specific AWS profile
python cloud_archaeologist.py --profile myprofile

# Specify output format
python cloud_archaeologist.py --output json
```

## Output

The tool generates:
- Console output showing the scanning progress
- A comprehensive text report saved as `cloud_archaeologist_report_YYYYMMDD_HHMMSS.txt`
- Cost breakdown by resource type
- Recommendations for cost optimization

## AWS Permissions Required

The tool requires the following AWS permissions:
- `ec2:DescribeRegions`
- `ec2:DescribeInstances`
- `ec2:DescribeVolumes`
- `ec2:DescribeAddresses`
- `ec2:DescribeSnapshots`
- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`
- `s3:ListBucket`

## Security Note

⚠️ **Important**: The demo script includes AWS credentials. In production, use IAM roles or AWS credentials file instead of hardcoding keys.

## Cost Calculation Method

The tool uses approximate pricing based on AWS on-demand rates. For more accurate pricing, consider:
- Reserved Instances
- Savings Plans
- Spot instances
- Volume discounts
- Regional variations

## License

This project is available for use under the MIT license.