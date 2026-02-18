#!/usr/bin/env python3
"""
Cloud Resource Archaeologist

A comprehensive tool that scans AWS resources including EC2, EBS, S3, EIP, and snapshots
with detailed cost calculations and professional reporting.
"""

import boto3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from botocore.exceptions import ClientError
import argparse
import sys
from typing import List, Dict, Any
import colorama
from colorama import Fore, Style, init
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

VERSION = "v1.0.0"


class CloudResourceArchaeologist:
    """
    Cloud Resource Archaeologist - A comprehensive AWS resource discovery and cost analysis tool.
    """

    def __init__(self, quiet=False, regions_to_scan=None):
        """Initialize the Cloud Resource Archaeologist with AWS clients."""
        self.quiet = quiet
        self.regions_to_scan = regions_to_scan  # List of regions to scan, or None for all

        # Suppress output if quiet mode is enabled
        if quiet:
            self.print_cyan = lambda x: None
            self.print_green = lambda x: None
            self.print_red = lambda x: None
            self.print_yellow = lambda x: None
        else:
            self.print_cyan = lambda x: print(Fore.CYAN + x)
            self.print_green = lambda x: print(Fore.GREEN + x)
            self.print_red = lambda x: print(Fore.RED + x)
            self.print_yellow = lambda x: print(Fore.YELLOW + x)

        # AWS credentials are loaded from:
        # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
        # 2. AWS credentials file (~/.aws/credentials)
        # 3. IAM roles (when running on EC2)
        #
        # Configure credentials before running:
        #   export AWS_ACCESS_KEY_ID=your_key
        #   export AWS_SECRET_ACCESS_KEY=your_secret
        #   export AWS_DEFAULT_REGION=us-east-1
        #
        # Or use: aws configure

        # Create clients for various AWS services
        self.ec2_client = boto3.client('ec2')
        self.s3_client = boto3.client('s3')
        self.ec2_resource = boto3.resource('ec2')
        self.ce_client = boto3.client('ce')  # Cost Explorer
        self.cloudwatch_client = boto3.client('cloudwatch')

        # Resource storage
        self.ec2_instances = []
        self.ebs_volumes = []
        self.s3_buckets = []
        self.eips = []
        self.snapshots = []

        # Cost constants (these would normally come from AWS pricing APIs)
        self.cost_constants = {
            'ec2': {
                't2.micro': 0.0116,  # per hour
                't2.small': 0.023,   # per hour
                't2.medium': 0.0467, # per hour
                't2.large': 0.093,   # per hour
                't3.micro': 0.0104,  # per hour
                't3.small': 0.0208,  # per hour
                't3.medium': 0.0416, # per hour
                't3.large': 0.0832,  # per hour
            },
            'ebs': {
                'gp2': 0.10,  # per GB-month
                'gp3': 0.08,  # per GB-month
                'io1': 0.125, # per GB-month
                'io2': 0.125, # per GB-month
                'st1': 0.045, # per GB-month
                'sc1': 0.015, # per GB-month
            },
            's3': {
                'standard': 0.023,  # per GB-month
                'intelligent_tiering': 0.0125,  # per GB-month first 50TB
                'standard_ia': 0.0125,  # per GB-month
                'onezone_ia': 0.01,  # per GB-month
                'glacier': 0.004,  # per GB-month
                'glacier_ir': 0.0036,  # per GB-month
            },
            'eip': {
                'hourly_rate': 0.005,  # per hour when not attached
            },
            'snapshot': {
                'per_gb_month': 0.05,  # per GB-month
            }
        }

    def discover_ec2_instances(self) -> List[Dict[str, Any]]:
        """Discover all EC2 instances across all regions."""
        if not self.quiet:
            self.print_cyan("[EC2] Discovering EC2 instances...")

        ec2_instances = []

        try:
            # Get all regions or use provided list
            if self.regions_to_scan:
                regions = self.regions_to_scan
            else:
                # Get all regions
                regions_response = self.ec2_client.describe_regions()
                regions = [region['RegionName'] for region in regions_response['Regions']]

            # Use tqdm for region scanning progress
            for region in tqdm(regions, desc="Scanning regions for EC2", disable=self.quiet, colour='cyan'):
                if not self.quiet:
                    self.print_cyan(f"  [REGION] Scanning region: {region}")

                ec2 = boto3.client('ec2', region_name=region)

                try:
                    # Describe all instances in the region
                    paginator = ec2.get_paginator('describe_instances')
                    page_iterator = paginator.paginate()

                    for page in page_iterator:
                        for reservation in page['Reservations']:
                            for instance in reservation['Instances']:
                                # Calculate running hours based on launch time
                                launch_time = instance.get('LaunchTime')
                                if launch_time:
                                    running_hours = (datetime.now(launch_time.tzinfo) - launch_time).total_seconds() / 3600
                                else:
                                    running_hours = 0

                                # Get instance cost
                                instance_type = instance.get('InstanceType', 'unknown')
                                hourly_cost = self.cost_constants['ec2'].get(instance_type, 0.05)  # Default cost if unknown type
                                monthly_cost = hourly_cost * 730  # 730 hours in a month

                                # Get instance tags
                                tags = instance.get('Tags', [])
                                name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'N/A')

                                ec2_instance = {
                                    'InstanceId': instance.get('InstanceId'),
                                    'InstanceType': instance_type,
                                    'State': instance['State']['Name'],
                                    'Region': region,
                                    'PublicIP': instance.get('PublicIpAddress', 'N/A'),
                                    'PrivateIP': instance.get('PrivateIpAddress', 'N/A'),
                                    'LaunchTime': launch_time.isoformat() if launch_time else 'N/A',
                                    'RunningHours': round(running_hours, 2),
                                    'HourlyCost': hourly_cost,
                                    'MonthlyCost': round(monthly_cost, 4),
                                    'Name': name_tag,
                                    'VpcId': instance.get('VpcId', 'N/A'),
                                    'SubnetId': instance.get('SubnetId', 'N/A'),
                                }

                                ec2_instances.append(ec2_instance)

                except ClientError as e:
                    self.print_red(f"    [WARNING] Error accessing region {region}: {str(e)}")
                    continue

        except ClientError as e:
            self.print_red(f"[ERROR] Error retrieving regions: {str(e)}")
            return []

        self.print_green(f"[SUCCESS] Found {len(ec2_instances)} EC2 instances")
        self.ec2_instances = ec2_instances
        return ec2_instances

    def discover_ebs_volumes(self) -> List[Dict[str, Any]]:
        """Discover all EBS volumes across all regions."""
        if not self.quiet:
            self.print_cyan("[EBS] Discovering EBS volumes...")

        ebs_volumes = []

        try:
            # Get all regions or use provided list
            if self.regions_to_scan:
                regions = self.regions_to_scan
            else:
                # Get all regions
                regions_response = self.ec2_client.describe_regions()
                regions = [region['RegionName'] for region in regions_response['Regions']]

            # Use tqdm for region scanning progress
            for region in tqdm(regions, desc="Scanning regions for EBS", disable=self.quiet, colour='cyan'):
                if not self.quiet:
                    self.print_cyan(f"  [REGION] Scanning region: {region}")

                ec2 = boto3.client('ec2', region_name=region)

                try:
                    # Describe all volumes in the region
                    paginator = ec2.get_paginator('describe_volumes')
                    page_iterator = paginator.paginate()

                    for page in page_iterator:
                        for volume in page['Volumes']:
                            # Get volume cost
                            volume_type = volume.get('VolumeType', 'gp2')
                            size_gb = volume.get('Size', 0)
                            monthly_cost = self.cost_constants['ebs'].get(volume_type, 0.10) * size_gb

                            # Get volume tags
                            tags = volume.get('Tags', [])
                            name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'N/A')

                            ebs_volume = {
                                'VolumeId': volume.get('VolumeId'),
                                'VolumeType': volume_type,
                                'Size': size_gb,
                                'State': volume.get('State'),
                                'Region': region,
                                'CreateTime': volume.get('CreateTime').isoformat(),
                                'MonthlyCost': round(monthly_cost, 4),
                                'Name': name_tag,
                                'Encrypted': volume.get('Encrypted', False),
                                'Iops': volume.get('Iops', 'N/A'),
                                'Throughput': volume.get('Throughput', 'N/A'),
                            }

                            ebs_volumes.append(ebs_volume)

                except ClientError as e:
                    self.print_red(f"    [WARNING] Error accessing region {region}: {str(e)}")
                    continue

        except ClientError as e:
            self.print_red(f"[ERROR] Error retrieving regions: {str(e)}")
            return []

        self.print_green(f"[SUCCESS] Found {len(ebs_volumes)} EBS volumes")
        self.ebs_volumes = ebs_volumes
        return ebs_volumes

    def discover_s3_buckets(self) -> List[Dict[str, Any]]:
        """Discover all S3 buckets and their properties."""
        if not self.quiet:
            self.print_cyan("[S3] Discovering S3 buckets...")

        s3_buckets = []

        try:
            # List all buckets
            response = self.s3_client.list_buckets()
            buckets = response['Buckets']

            # Use tqdm for resource discovery progress
            for bucket in tqdm(buckets, desc="Discovering S3 buckets", disable=self.quiet, colour='cyan'):
                bucket_name = bucket['Name']
                creation_date = bucket['CreationDate'].isoformat()

                # Get bucket region
                try:
                    location_response = self.s3_client.get_bucket_location(Bucket=bucket_name)
                    region = location_response.get('LocationConstraint')
                    if region is None:
                        region = 'us-east-1'  # Default region for us-east-1
                    else:
                        region = region
                except ClientError as e:
                    self.print_red(f"    [WARNING] Could not get region for bucket {bucket_name}: {str(e)}")
                    region = 'unknown'
                    continue

                # Get bucket size (approximate)
                try:
                    size_gb = 0
                    objects_response = self.s3_client.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in objects_response:
                        for obj in objects_response['Contents']:
                            size_gb += obj['Size']
                    size_gb = size_gb / (1024 * 1024 * 1024)  # Convert to GB
                except ClientError as e:
                    self.print_red(f"    [WARNING] Could not get size for bucket {bucket_name}: {str(e)}")
                    size_gb = 0

                # Calculate approximate monthly cost (this is a rough estimate)
                monthly_cost = size_gb * self.cost_constants['s3']['standard']

                s3_bucket = {
                    'Name': bucket_name,
                    'CreationDate': creation_date,
                    'Region': region,
                    'SizeGB': round(size_gb, 4),
                    'MonthlyCost': round(monthly_cost, 4),
                    'Policy': 'N/A',  # Would need to check bucket policy
                    'Versioning': 'N/A',  # Would need to check versioning status
                    'Encryption': 'N/A',  # Would need to check encryption status
                }

                s3_buckets.append(s3_bucket)

        except ClientError as e:
            self.print_red(f"[ERROR] Error retrieving S3 buckets: {str(e)}")
            return []

        self.print_green(f"[SUCCESS] Found {len(s3_buckets)} S3 buckets")
        self.s3_buckets = s3_buckets
        return s3_buckets

    def discover_eips(self) -> List[Dict[str, Any]]:
        """Discover all Elastic IP addresses."""
        if not self.quiet:
            self.print_cyan("[EIP] Discovering Elastic IPs...")

        eips = []

        try:
            # Get all regions or use provided list
            if self.regions_to_scan:
                regions = self.regions_to_scan
            else:
                # Get all regions
                regions_response = self.ec2_client.describe_regions()
                regions = [region['RegionName'] for region in regions_response['Regions']]

            # Use tqdm for region scanning progress
            for region in tqdm(regions, desc="Scanning regions for EIP", disable=self.quiet, colour='cyan'):
                if not self.quiet:
                    self.print_cyan(f"  [REGION] Scanning region: {region}")

                ec2 = boto3.client('ec2', region_name=region)

                try:
                    # Describe all EIPs in the region
                    response = ec2.describe_addresses()

                    for address in response['Addresses']:
                        # Calculate monthly cost based on whether EIP is associated
                        is_associated = address.get('InstanceId') or address.get('NetworkInterfaceId') or address.get('AssociationId')
                        hourly_rate = 0 if is_associated else self.cost_constants['eip']['hourly_rate']
                        monthly_cost = hourly_rate * 730  # 730 hours in a month

                        eip = {
                            'PublicIp': address.get('PublicIp'),
                            'AllocationId': address.get('AllocationId'),
                            'Domain': address.get('Domain'),
                            'Region': region,
                            'InstanceId': address.get('InstanceId', 'N/A'),
                            'NetworkInterfaceId': address.get('NetworkInterfaceId', 'N/A'),
                            'IsAssociated': is_associated,
                            'HourlyCost': hourly_rate,
                            'MonthlyCost': round(monthly_cost, 4),
                        }

                        eips.append(eip)

                except ClientError as e:
                    self.print_red(f"    [WARNING] Error accessing region {region}: {str(e)}")
                    continue

        except ClientError as e:
            self.print_red(f"[ERROR] Error retrieving regions: {str(e)}")
            return []

        self.print_green(f"[SUCCESS] Found {len(eips)} Elastic IPs")
        self.eips = eips
        return eips

    def discover_snapshots(self) -> List[Dict[str, Any]]:
        """Discover all EBS snapshots."""
        if not self.quiet:
            self.print_cyan("[SNAPSHOT] Discovering EBS snapshots...")

        snapshots = []

        try:
            # Get all regions or use provided list
            if self.regions_to_scan:
                regions = self.regions_to_scan
            else:
                # Get all regions
                regions_response = self.ec2_client.describe_regions()
                regions = [region['RegionName'] for region in regions_response['Regions']]

            # Use tqdm for region scanning progress
            for region in tqdm(regions, desc="Scanning regions for snapshots", disable=self.quiet, colour='cyan'):
                if not self.quiet:
                    self.print_cyan(f"  [REGION] Scanning region: {region}")

                ec2 = boto3.client('ec2', region_name=region)

                try:
                    # Describe all snapshots in the region (only owned by the account)
                    paginator = ec2.get_paginator('describe_snapshots')
                    page_iterator = paginator.paginate(OwnerIds=['self'])

                    for page in page_iterator:
                        for snapshot in page['Snapshots']:
                            # Get snapshot size and calculate cost
                            volume_size = snapshot.get('VolumeSize', 0)  # in GB
                            # Calculate cost based on size (simplified)
                            monthly_cost = volume_size * self.cost_constants['snapshot']['per_gb_month']

                            # Get snapshot tags
                            tags = snapshot.get('Tags', [])
                            name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'N/A')

                            snap = {
                                'SnapshotId': snapshot.get('SnapshotId'),
                                'VolumeId': snapshot.get('VolumeId', 'N/A'),
                                'State': snapshot.get('State'),
                                'StartTime': snapshot.get('StartTime').isoformat(),
                                'VolumeSize': volume_size,
                                'Region': region,
                                'Description': snapshot.get('Description', 'N/A'),
                                'Name': name_tag,
                                'MonthlyCost': round(monthly_cost, 4),
                            }

                            snapshots.append(snap)

                except ClientError as e:
                    self.print_red(f"    [WARNING] Error accessing region {region}: {str(e)}")
                    continue

        except ClientError as e:
            self.print_red(f"[ERROR] Error retrieving regions: {str(e)}")
            return []

        self.print_green(f"[SUCCESS] Found {len(snapshots)} snapshots")
        self.snapshots = snapshots
        return snapshots

    def calculate_total_costs(self) -> Dict[str, float]:
        """Calculate total costs for all resource types."""
        if not self.quiet:
            self.print_cyan("[COST] Calculating total costs...")

        total_ec2 = sum(instance['MonthlyCost'] for instance in self.ec2_instances)
        total_ebs = sum(volume['MonthlyCost'] for volume in self.ebs_volumes)
        total_s3 = sum(bucket['MonthlyCost'] for bucket in self.s3_buckets)
        total_eip = sum(eip['MonthlyCost'] for eip in self.eips)
        total_snapshots = sum(snapshot['MonthlyCost'] for snapshot in self.snapshots)

        total_cost = total_ec2 + total_ebs + total_s3 + total_eip + total_snapshots

        cost_summary = {
            'EC2': total_ec2,
            'EBS': total_ebs,
            'S3': total_s3,
            'EIP': total_eip,
            'Snapshots': total_snapshots,
            'Total': total_cost
        }

        self.print_green(f"[SUCCESS] Total monthly cost: ${total_cost:.2f}")
        return cost_summary

    def generate_report(self, output_format='txt', output_filename=None) -> str:
        """Generate a professional report of all findings."""
        if not self.quiet:
            self.print_cyan("[REPORT] Generating professional report...")

        # Calculate totals
        cost_summary = self.calculate_total_costs()

        # Create report header
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CLOUD RESOURCE ARCHAEOLOGIST REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary section
        report_lines.append("SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"Total Resources Found:")
        report_lines.append(f"  EC2 Instances: {len(self.ec2_instances)}")
        report_lines.append(f"  EBS Volumes: {len(self.ebs_volumes)}")
        report_lines.append(f"  S3 Buckets: {len(self.s3_buckets)}")
        report_lines.append(f"  Elastic IPs: {len(self.eips)}")
        report_lines.append(f"  Snapshots: {len(self.snapshots)}")
        report_lines.append("")

        # Cost summary
        report_lines.append("COST SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"EC2 Monthly Cost: ${cost_summary['EC2']:.2f}")
        report_lines.append(f"EBS Monthly Cost: ${cost_summary['EBS']:.2f}")
        report_lines.append(f"S3 Monthly Cost: ${cost_summary['S3']:.2f}")
        report_lines.append(f"EIP Monthly Cost: ${cost_summary['EIP']:.2f}")
        report_lines.append(f"Snapshot Monthly Cost: ${cost_summary['Snapshots']:.2f}")
        report_lines.append(f"TOTAL Monthly Cost: ${cost_summary['Total']:.2f}")
        report_lines.append("")

        # EC2 instances details
        if self.ec2_instances:
            report_lines.append("EC2 INSTANCES")
            report_lines.append("-" * 20)
            report_lines.append(f"{'Instance ID':<20} {'Type':<15} {'State':<12} {'Region':<15} {'Monthly Cost':<15} {'Name':<20}")
            report_lines.append("-" * 100)
            for instance in tqdm(self.ec2_instances, desc="Generating EC2 report", disable=self.quiet, colour='blue'):
                report_lines.append(
                    f"{instance['InstanceId']:<20} "
                    f"{instance['InstanceType']:<15} "
                    f"{instance['State']:<12} "
                    f"{instance['Region']:<15} "
                    f"${instance['MonthlyCost']:<14.2f} "
                    f"{instance['Name']:<20}"
                )
            report_lines.append("")

        # EBS volumes details
        if self.ebs_volumes:
            report_lines.append("EBS VOLUMES")
            report_lines.append("-" * 20)
            report_lines.append(f"{'Volume ID':<20} {'Type':<10} {'Size (GB)':<12} {'State':<12} {'Region':<15} {'Monthly Cost':<15} {'Name':<20}")
            report_lines.append("-" * 100)
            for volume in tqdm(self.ebs_volumes, desc="Generating EBS report", disable=self.quiet, colour='blue'):
                report_lines.append(
                    f"{volume['VolumeId']:<20} "
                    f"{volume['VolumeType']:<10} "
                    f"{volume['Size']:<12} "
                    f"{volume['State']:<12} "
                    f"{volume['Region']:<15} "
                    f"${volume['MonthlyCost']:<14.2f} "
                    f"{volume['Name']:<20}"
                )
            report_lines.append("")

        # S3 buckets details
        if self.s3_buckets:
            report_lines.append("S3 BUCKETS")
            report_lines.append("-" * 20)
            report_lines.append(f"{'Bucket Name':<30} {'Region':<15} {'Size (GB)':<15} {'Monthly Cost':<15}")
            report_lines.append("-" * 80)
            for bucket in tqdm(self.s3_buckets, desc="Generating S3 report", disable=self.quiet, colour='blue'):
                report_lines.append(
                    f"{bucket['Name']:<30} "
                    f"{bucket['Region']:<15} "
                    f"{bucket['SizeGB']:<15.2f} "
                    f"${bucket['MonthlyCost']:<14.2f}"
                )
            report_lines.append("")

        # EIP details
        if self.eips:
            report_lines.append("ELASTIC IPs")
            report_lines.append("-" * 20)
            report_lines.append(f"{'Public IP':<15} {'Region':<15} {'Associated':<12} {'Monthly Cost':<15}")
            report_lines.append("-" * 70)
            for eip in tqdm(self.eips, desc="Generating EIP report", disable=self.quiet, colour='blue'):
                report_lines.append(
                    f"{eip['PublicIp']:<15} "
                    f"{eip['Region']:<15} "
                    f"{'Yes' if eip['IsAssociated'] else 'No':<12} "
                    f"${eip['MonthlyCost']:<14.2f}"
                )
            report_lines.append("")

        # Snapshot details
        if self.snapshots:
            report_lines.append("SNAPSHOTS")
            report_lines.append("-" * 20)
            report_lines.append(f"{'Snapshot ID':<25} {'Volume ID':<20} {'State':<12} {'Size (GB)':<12} {'Region':<15} {'Monthly Cost':<15} {'Name':<20}")
            report_lines.append("-" * 110)
            for snapshot in tqdm(self.snapshots, desc="Generating snapshot report", disable=self.quiet, colour='blue'):
                report_lines.append(
                    f"{snapshot['SnapshotId']:<25} "
                    f"{snapshot['VolumeId']:<20} "
                    f"{snapshot['State']:<12} "
                    f"{snapshot['VolumeSize']:<12} "
                    f"{snapshot['Region']:<15} "
                    f"${snapshot['MonthlyCost']:<14.2f} "
                    f"{snapshot['Name']:<20}"
                )
            report_lines.append("")

        # Recommendations section
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 20)

        # Check for unused resources
        unused_ec2 = [inst for inst in self.ec2_instances if inst['State'] == 'stopped']
        unattached_ebs = [vol for vol in self.ebs_volumes if vol['State'] == 'available']
        unassociated_eips = [eip for eip in self.eips if not eip['IsAssociated']]

        if unused_ec2:
            recommendation = f"[WARNING] Found {len(unused_ec2)} stopped EC2 instances that may be costing money"
            report_lines.append(recommendation)
            if not self.quiet:
                self.print_yellow(recommendation)

        if unattached_ebs:
            recommendation = f"[WARNING] Found {len(unattached_ebs)} unattached EBS volumes that may be costing money"
            report_lines.append(recommendation)
            if not self.quiet:
                self.print_yellow(recommendation)

        if unassociated_eips:
            recommendation = f"[WARNING] Found {len(unassociated_eips)} unassociated Elastic IPs that are incurring charges"
            report_lines.append(recommendation)
            if not self.quiet:
                self.print_yellow(recommendation)

        if not unused_ec2 and not unattached_ebs and not unassociated_eips:
            success_msg = "[SUCCESS] No obviously unused resources found"
            report_lines.append(success_msg)
            if not self.quiet:
                self.print_green(success_msg)

        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        report_str = "\n".join(report_lines)

        # Determine filename based on output format and optional output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_filename:
            # Use the provided output filename
            if output_format.lower() == 'csv' and not output_filename.endswith('.csv'):
                filename = f"{output_filename}.csv"
            elif output_format.lower() == 'json' and not output_filename.endswith('.json'):
                filename = f"{output_filename}.json"
            elif output_format.lower() == 'txt' and not output_filename.endswith('.txt'):
                filename = f"{output_filename}.txt"
            else:
                filename = output_filename
        else:
            # Generate filename based on format and timestamp
            if output_format.lower() == 'csv':
                filename = f"cloud_archaeologist_report_{timestamp}.csv"
            elif output_format.lower() == 'json':
                filename = f"cloud_archaeologist_report_{timestamp}.json"
            else:  # Default to TXT
                filename = f"cloud_archaeologist_report_{timestamp}.txt"

        if output_format.lower() == 'csv':
            # Convert report to CSV format
            import io
            import csv

            output = io.StringIO()
            writer = csv.writer(output)

            # Write all report lines as rows
            for line in report_lines:
                if line.strip():
                    # Try to detect table headers and split appropriately
                    if '|' in line:
                        row_data = [cell.strip() for cell in line.split('|')]
                    else:
                        row_data = [line]
                    writer.writerow(row_data)

            csv_content = output.getvalue()
            output.close()

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(csv_content)

        elif output_format.lower() == 'json':
            # Convert all data to JSON format
            report_json = {
                'metadata': {
                    'generated_on': datetime.now().isoformat(),
                    'version': VERSION
                },
                'summary': {
                    'total_ec2_instances': len(self.ec2_instances),
                    'total_ebs_volumes': len(self.ebs_volumes),
                    'total_s3_buckets': len(self.s3_buckets),
                    'total_eips': len(self.eips),
                    'total_snapshots': len(self.snapshots)
                },
                'cost_summary': self.calculate_total_costs(),
                'resources': {
                    'ec2_instances': self.ec2_instances,
                    'ebs_volumes': self.ebs_volumes,
                    's3_buckets': self.s3_buckets,
                    'elastic_ips': self.eips,
                    'snapshots': self.snapshots
                },
                'recommendations': {
                    'unused_ec2_instances': len([inst for inst in self.ec2_instances if inst['State'] == 'stopped']),
                    'unattached_ebs_volumes': len([vol for vol in self.ebs_volumes if vol['State'] == 'available']),
                    'unassociated_eips': len([eip for eip in self.eips if not eip['IsAssociated']])
                }
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_json, f, indent=2, default=str)
        else:  # Default to TXT
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_str)

        self.print_green(f"[SUCCESS] Report saved to {filename}")
        return report_str if output_format.lower() == 'txt' else f"[SUCCESS] {output_format.upper()} report saved to {filename}"

    def run_full_scan(self, output_format='txt', services_to_scan=None, output_filename=None):
        """Run a scan of AWS resources with specified services and regions."""
        if not self.quiet:
            self.print_cyan("[SCAN] Starting Cloud Resource Archaeologist scan...")
            if services_to_scan:
                self.print_cyan(f"[SCAN] Scanning services: {', '.join(services_to_scan)}")
            if self.regions_to_scan:
                self.print_cyan(f"[SCAN] Scanning regions: {', '.join(self.regions_to_scan)}")
            self.print_cyan("")

        # If no services specified, scan all
        if not services_to_scan:
            services_to_scan = ['ec2', 'ebs', 's3', 'eip', 'snapshots']

        # Discover resources based on specified services
        if 'ec2' in services_to_scan:
            self.discover_ec2_instances()
            if not self.quiet:
                self.print_cyan("")

        if 'ebs' in services_to_scan:
            self.discover_ebs_volumes()
            if not self.quiet:
                self.print_cyan("")

        if 's3' in services_to_scan:
            self.discover_s3_buckets()
            if not self.quiet:
                self.print_cyan("")

        if 'eip' in services_to_scan:
            self.discover_eips()
            if not self.quiet:
                self.print_cyan("")

        if 'snapshots' in services_to_scan:
            self.discover_snapshots()
            if not self.quiet:
                self.print_cyan("")

        # Generate the report
        report = self.generate_report(output_format, output_filename)

        if not self.quiet:
            self.print_cyan("")
        self.print_green("[SUCCESS] Cloud Resource Archaeologist scan completed!")
        self.print_green(f"[SUMMARY] Total resources discovered: {len(self.ec2_instances) + len(self.ebs_volumes) + len(self.s3_buckets) + len(self.eips) + len(self.snapshots)}")
        self.print_green(f"[COST] Total estimated monthly cost: ${sum(self.calculate_total_costs().values()) - self.calculate_total_costs()['Total'] + self.calculate_total_costs()['Total']:.2f}")


def main():
    """Main function to run the Cloud Resource Archaeologist."""
    parser = argparse.ArgumentParser(description='Cloud Resource Archaeologist - AWS Resource Discovery and Cost Analysis')
    parser.add_argument('--profile', type=str, help='AWS profile name to use')
    parser.add_argument('--services', type=str, help='Services to scan: ec2, ebs, s3, eip, snapshots, or all (comma-separated)')
    parser.add_argument('--regions', type=str, help='Regions to scan (comma-separated) or "all" (default: all regions)')
    parser.add_argument('--no-cost', action='store_true', help='Skip AWS pricing calculations')
    parser.add_argument('--output', type=str, help='Output filename for the report')
    parser.add_argument('--format', type=str, choices=['txt', 'csv', 'json'], default='txt', help='Output format: txt, csv, or json (default: txt)')
    parser.add_argument('--quiet', action='store_true', help='Run in quiet mode with minimal output')
    parser.add_argument('--version', action='store_true', help='Show version')

    args = parser.parse_args()

    if args.version:
        print(f"Cloud Archaeologist {VERSION}")
        return

    # Set up AWS credentials/profile if specified
    if args.profile:
        boto3.setup_default_session(profile_name=args.profile)

    # Process services argument
    services_to_scan = ['ec2', 'ebs', 's3', 'eip', 'snapshots']  # default to all
    if args.services:
        services_to_scan = [s.strip().lower() for s in args.services.split(',')]
        # Validate services
        valid_services = {'ec2', 'ebs', 's3', 'eip', 'snapshots', 'all'}
        if 'all' in services_to_scan:
            services_to_scan = ['ec2', 'ebs', 's3', 'eip', 'snapshots']
        else:
            invalid_services = [s for s in services_to_scan if s not in valid_services]
            if invalid_services:
                print(f"Error: Invalid services specified: {invalid_services}")
                sys.exit(1)

    # Process regions argument
    regions_to_scan = None  # None means all regions
    if args.regions:
        if args.regions.lower() == 'all':
            regions_to_scan = None  # scan all regions
        else:
            regions_to_scan = [r.strip() for r in args.regions.split(',')]

    # Process no-cost argument
    skip_cost_calculations = args.no_cost

    # Create and run the archaeologist with regions to scan
    archaeologist = CloudResourceArchaeologist(quiet=args.quiet, regions_to_scan=regions_to_scan)

    try:
        # Modify archaeologist behavior based on no-cost argument
        if skip_cost_calculations:
            # Temporarily modify cost constants to zero for cost calculation
            archaeologist.cost_constants = {
                'ec2': {k: 0 for k in archaeologist.cost_constants['ec2']},
                'ebs': {k: 0 for k in archaeologist.cost_constants['ebs']},
                's3': {k: 0 for k in archaeologist.cost_constants['s3']},
                'eip': {'hourly_rate': 0},
                'snapshot': {'per_gb_month': 0}
            }

        # Run the full scan with all parameters
        archaeologist.run_full_scan(
            output_format=args.format,
            services_to_scan=services_to_scan,
            output_filename=args.output
        )

    except KeyboardInterrupt:
        if not archaeologist.quiet:
            archaeologist.print_red("\n[WARNING] Scan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        if not archaeologist.quiet:
            archaeologist.print_red(f"[ERROR] Error during scan: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()