# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os
import boto3,time
import logging,json
import yaml

def read_yaml(file_path):
    # Read YAML file
    data_loaded=None
    with open(file_path, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    return data_loaded
logger=logging
region="ap-south-1"
creds_file_path="/Users/mohamed.hafeez.ext/Documents/infra-switch/cred.yaml"
creds = read_yaml(creds_file_path)
boto3 = boto3.Session(
        aws_access_key_id=creds['aws']['aws_access_key_id'],
        aws_secret_access_key=creds['aws']['aws_secret_access_key'],
        aws_session_token=creds['aws']['aws_session_token'],
        profile_name=creds['aws']['profile_name']
        )

input = '''{
    "db_instance_identifier": "test-aws-db-1",
    "target_engine_version": "11.20",
    "new_parameter_group_name": "test-sre-db-11",
    "Replica_DB_Identifier": "test-aws-db-2",
    "DNS_Record_Name": "db.juspay.local",
    "metadata": {
        "region": "ap-south-1"
    }
}'''

def getinput(input):
    try:
        context = json.loads(input)
        db_instance_identifier = context.get("db_instance_identifier")
        region = context.get("metadata").get("region")
        target_engine_version = context.get("target_engine_version")
        new_parameter_group_name = context.get("new_parameter_group_name")
        replica_db_identifier= context.get("Replica_DB_Identifier")
        dns_record_name= context.get("DNS_Record_Name")
    except Exception as e:
        logger.error("There's an issue with input: " + str(e))
    return [db_instance_identifier, region, str(target_engine_version),new_parameter_group_name,replica_db_identifier,dns_record_name]


def wait_until_instance_active(replica_db_identifier):
        try:
            while True:
                rds_client = boto3.client('rds', region)
                response = rds_client.describe_db_instances(
                    DBInstanceIdentifier=replica_db_identifier
                )
                if 'DBInstances' in response and len(response['DBInstances']) > 0:
                    instance_status = response['DBInstances'][0]['DBInstanceStatus']
                    logger.info(f"Current instance status: {instance_status}")
                    if instance_status == 'available':
                        logger.info(f"Instance is active.")
                        return True
                else:
                    logger.error(f"Instance details not found.")
                time.sleep(10)
        except Exception as error:
            logger.error(error, exc_info=True)
            return False

def validate_db_upgrade(replica_db_identifier,target_engine_version):
    try:
        rds_client = boto3.client('rds', region)
        response = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            if 'EngineVersion' in instance:
                if str(instance['EngineVersion']) == str(target_engine_version):
                    return (instance['EngineVersion'])
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error validating DB upgrade: {e}")
        return False

def get_rds_endpoint(instance_identifier):
    try:
        rds_client = boto3.client('rds',region)
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_identifier)
        
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            endpoint = instance.get('Endpoint', {}).get('Address')
            return endpoint
        else:
            print(f"Instance '{instance_identifier}' not found.")
            return None

    except Exception as e:
        print(f"Error getting RDS endpoint: {e}")
        return None

def check_route53_for_rds_dns(record_name,db_instance_identifier,replica_db_identifier):
    try:
        route53_client = boto3.client('route53')
        response = route53_client.list_hosted_zones()
        hosted_zones = response['HostedZones']

        rds_dns = get_rds_endpoint(db_instance_identifier)
        rds_new_dns=get_rds_endpoint(replica_db_identifier)
        for zone in hosted_zones:
            response = route53_client.list_resource_record_sets(
                HostedZoneId=zone['Id'],
                StartRecordName=record_name,
                MaxItems='1'
            )
            if 'ResourceRecordSets' in response and len(response['ResourceRecordSets']) > 0:
                record_set = response['ResourceRecordSets'][0]
                print(record_set)
                if rds_dns == record_set['ResourceRecords'][0]['Value']:
                    #record_set['Name'] = record_name 
                    print("The Route 53 record value matches the RDS endpoint DNS.")
                    return "In-progress"
                elif rds_new_dns == record_set['ResourceRecords'][0]['Value']:
                    print("The Route 53 record matches the New RDS endpoint DNS.")
                    return True

        print("No matching record found for the record for RDS Endpoint.")
        return False
    except Exception as e:
        print(f"Error checking Route 53 for RDS DNS: {e}")


if __name__ == "__main__":
    try:
        db_instance_identifier,region,target_engine_version,new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        stage_input = True
        if stage_input == True:
            while True:
                response=wait_until_instance_active(replica_db_identifier)
                if response:
                    logger.info(f"Instance -  {replica_db_identifier} is Active.")
                    response=validate_db_upgrade(replica_db_identifier,target_engine_version)
                    if response == target_engine_version:
                        record_name = "db2.juspay.local"
                        response2=check_route53_for_rds_dns(dns_record_name,db_instance_identifier,replica_db_identifier)
                        if response2 == True:
                            print("The RDS Endpoint is flipped")
                            print({
                            "output": {
                                "success": "SUCCESSFUL",
                                "message": "Healthy Instance Post Upgrade.",
                            },
                            "nextStageInput": {"Result": True},
                            })
                        elif response2 == "In-progress":
                            print("The RDS Endpoint is not flipped yet")
                            print({
                            "output": {
                                "success": "IN-PROGRESS",
                                "message": "DNS ROUTE FOR RDS IS NOT FLIPPED.",
                            },
                            "nextStageInput": {},
                            })
                        break
                    else:
                        print({
                            "output": {
                                "success": "FAILED",
                                "message": "Upgrade to Target version was unsuccessful.",
                            },
                            "nextStageInput": {"Result": False},
                            })
                        break
                        

    except Exception as error:
        logger.error(error, exc_info=True)
        print({
            "output": {
                "success": "FAILED",
                "message": "Caught an exception.",
            },
              "nextStageInput": {"Result": False},
        })




