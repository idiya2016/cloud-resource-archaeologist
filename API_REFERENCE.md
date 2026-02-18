# Cloud Archaeologist - API Reference

## Command Line Interface

### Main Command
```bash
python cloud_archaeologist.py [OPTIONS]
```

### Available Options

#### `--profile`
- **Description**: AWS profile name to use for authentication
- **Type**: String
- **Example**: `--profile myprofile`

#### `--region`
- **Description**: AWS region to scan (default: all regions)
- **Type**: String
- **Example**: `--region us-west-2`

#### `--format`
- **Description**: Output format for the report
- **Type**: String (choices: txt, csv, json)
- **Default**: txt
- **Example**: `--format json`

#### `--quiet`
- **Description**: Run in quiet mode with minimal output
- **Type**: Boolean flag
- **Example**: `--quiet`

#### `--version`
- **Description**: Show version information
- **Type**: Boolean flag
- **Example**: `--version`

### Examples

#### Basic Usage
```bash
python cloud_archaeologist.py
```

#### Scan with specific format
```bash
python cloud_archaeologist.py --format json
```

#### Quiet mode with specific region
```bash
python cloud_archaeologist.py --region us-east-1 --quiet
```

#### Using AWS profile
```bash
python cloud_archaeologist.py --profile myprofile --format csv
```

## Class Structure

### CloudResourceArchaeologist

#### Constructor
```python
CloudResourceArchaeologist(quiet=False)
```
- **quiet**: Optional boolean to enable quiet mode (default: False)

#### Methods

##### `discover_ec2_instances()`
- **Description**: Discovers all EC2 instances across all regions
- **Returns**: List of EC2 instance dictionaries
- **Properties**: InstanceId, InstanceType, State, Region, PublicIP, PrivateIP, LaunchTime, RunningHours, HourlyCost, MonthlyCost, Name, VpcId, SubnetId

##### `discover_ebs_volumes()`
- **Description**: Discovers all EBS volumes across all regions
- **Returns**: List of EBS volume dictionaries
- **Properties**: VolumeId, VolumeType, Size, State, Region, CreateTime, MonthlyCost, Name, Encrypted, Iops, Throughput

##### `discover_s3_buckets()`
- **Description**: Discovers all S3 buckets and their properties
- **Returns**: List of S3 bucket dictionaries
- **Properties**: Name, CreationDate, Region, SizeGB, MonthlyCost, Policy, Versioning, Encryption

##### `discover_eips()`
- **Description**: Discovers all Elastic IP addresses
- **Returns**: List of EIP dictionaries
- **Properties**: PublicIp, AllocationId, Domain, Region, InstanceId, NetworkInterfaceId, IsAssociated, HourlyCost, MonthlyCost

##### `discover_snapshots()`
- **Description**: Discovers all EBS snapshots
- **Returns**: List of snapshot dictionaries
- **Properties**: SnapshotId, VolumeId, State, StartTime, VolumeSize, Region, Description, Name, MonthlyCost

##### `calculate_total_costs()`
- **Description**: Calculates total costs for all resource types
- **Returns**: Dictionary with cost summary for each resource type and total

##### `generate_report(output_format='txt')`
- **Description**: Generates a professional report of all findings
- **Parameters**: 
  - `output_format`: Output format (txt, csv, or json)
- **Returns**: Report string (or confirmation message for non-txt formats)

##### `run_full_scan(output_format='txt')`
- **Description**: Runs a complete scan of all AWS resources
- **Parameters**: 
  - `output_format`: Output format (txt, csv, or json)

## Cost Constants

The tool uses predefined cost constants for different AWS resources:

### EC2 Instance Costs (per hour)
- t2.micro: $0.0116
- t2.small: $0.023
- t2.medium: $0.0467
- t2.large: $0.093
- t3.micro: $0.0104
- t3.small: $0.0208
- t3.medium: $0.0416
- t3.large: $0.0832

### EBS Volume Costs (per GB-month)
- gp2: $0.10
- gp3: $0.08
- io1: $0.125
- io2: $0.125
- st1: $0.045
- sc1: $0.015

### S3 Storage Costs (per GB-month)
- standard: $0.023
- intelligent_tiering: $0.0125
- standard_ia: $0.0125
- onezone_ia: $0.01
- glacier: $0.004
- glacier_ir: $0.0036

### EIP Costs
- Hourly rate when not attached: $0.005

### Snapshot Costs
- Per GB-month: $0.05