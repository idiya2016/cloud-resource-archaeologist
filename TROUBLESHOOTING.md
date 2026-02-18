# Cloud Archaeologist - Troubleshooting Guide

## Common Issues and Solutions

### 1. AWS Authentication Errors

**Problem**: `botocore.exceptions.ClientError: Operation not allowed`
**Solution**: 
- Verify AWS credentials are properly configured
- Check IAM permissions (see AWS_IAM_POLICY.json)
- Ensure the AWS profile exists and is correctly specified

**Problem**: `NoCredentialsError: Unable to locate credentials`
**Solution**:
- Run `aws configure` to set up credentials
- Or set environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Or verify `~/.aws/credentials` file exists and is properly formatted

### 2. Permission Issues

**Problem**: `AccessDenied` errors during scan
**Solution**:
- Ensure your IAM user/role has all required permissions (see AWS_IAM_POLICY.json)
- Verify that the policy is attached to your user or role
- Check if the account is in an AWS Organizations organization with service control policies that might restrict access

### 3. Installation Issues

**Problem**: `ModuleNotFoundError` for dependencies
**Solution**:
```bash
pip install -r requirements.txt
```
Or install packages individually:
```bash
pip install boto3 colorama tqdm
```

**Problem**: `PermissionError` during installation
**Solution**:
- Use virtual environment: `python -m venv venv && source venv/bin/activate`
- Or use `--user` flag: `pip install --user -r requirements.txt`

### 4. Network/Connection Issues

**Problem**: `SSLError` or connection timeouts
**Solution**:
- Check network connectivity to AWS endpoints
- Verify proxy settings if behind corporate firewall
- Try using a different region or network connection

**Problem**: `ReadTimeoutError`
**Solution**:
- Increase timeout settings in boto3 configuration
- Retry the operation
- Check AWS service availability in the affected regions

### 5. Performance Issues

**Problem**: Script takes too long to complete
**Solution**:
- The tool scans all regions; consider specifying a specific region with `--region`
- Use `--quiet` flag to reduce output overhead
- Ensure good network connectivity to AWS

**Problem**: High memory usage
**Solution**:
- The tool processes large amounts of AWS resource data
- Consider scanning during off-peak hours
- Monitor system resources during execution

## Debugging Tips

### Enable Verbose Logging
If using with AWS SDK directly, you can enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check AWS Service Status
Visit [AWS Service Health Dashboard](https://status.aws.amazon.com/) to check for any ongoing issues with AWS services.

### Verify API Calls
The tool uses these AWS APIs:
- EC2: `describe_instances`, `describe_volumes`, `describe_addresses`, `describe_snapshots`, `describe_regions`
- S3: `list_buckets`, `get_bucket_location`, `list_objects_v2`
- CloudWatch: `get_metric_statistics` (if used)
- Cost Explorer: `get_cost_and_usage` (if used)

## Reporting Problems

If you encounter an issue not covered in this guide:

1. Verify you're using the latest version of the tool
2. Check that all dependencies are up-to-date
3. Ensure your AWS credentials and permissions are correct
4. If the problem persists, create an issue in the repository with:
   - Python version (`python --version`)
   - Cloud Archaeologist version (`python cloud_archaeologist.py --version`)
   - Operating system
   - Command used
   - Full error message
   - Any relevant environment information

## Preventive Measures

### Before Running
- Ensure sufficient IAM permissions
- Verify network connectivity to AWS
- Check available disk space for reports (reports are typically under 10MB)

### During Execution
- Monitor system resources
- Allow adequate time (scans can take several minutes depending on resources)
- Don't interrupt the process unless necessary

### After Execution
- Verify report was generated successfully
- Check report for completeness
- Store reports securely as they may contain sensitive information

## Quick Fixes

| Issue | Command to Try |
|-------|----------------|
| Permission denied | `aws configure` |
| Missing modules | `pip install -r requirements.txt` |
| Outdated version | `git pull origin main` |
| SSL errors | Check proxy settings or network |
| Slow performance | Use `--region` to limit scope |

## Support Resources

- [AWS Documentation](https://docs.aws.amazon.com/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- Cloud Archaeologist repository issues
- Python AWS SDK community forums