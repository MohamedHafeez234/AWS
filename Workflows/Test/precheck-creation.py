import boto3
import time
import logging
import yaml
import json

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
    "db_instance_identifier": "test-aws-db",
    "target_engine_version": "14.4",
    "new_parameter_group_name": "test-sre-db-13",
    "Replica_DB_Identifier": "test-aws-db-2",
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
    except Exception as e:
        logger.error("There's an issue with input: " + str(e))
    return [db_instance_identifier, region, str(target_engine_version), new_parameter_group_name,replica_db_identifier]

def get_rds_instance_details(instance_name):
    try:
        rds_client = boto3.client('rds',region)
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_name)
        # Find the instance with the specified name
        for instance in response['DBInstances']:
            if instance['DBInstanceIdentifier'] == instance_name:
                return instance
        # If the instance is not found, return None
        return None

    except Exception as e:
        print("Error occurred while getting RDS instance details:", str(e))
        return None

def check_read_replica_present(db_instance_identifier, replica_db_identifier):
    try:
        rds_client = boto3.client('rds', region)
        source_response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        if 'DBInstances' in source_response:
            source_instance = source_response['DBInstances'][0]
            if 'ReadReplicaDBInstanceIdentifiers' in source_instance:
                replica_identifiers = source_instance['ReadReplicaDBInstanceIdentifiers']
                if replica_db_identifier in replica_identifiers:
                    return True
            else:
                return False
        else:
            return False
        
    except Exception as e:
        print(f"Error checking read replica presence: {e}")
        return False

if __name__ == "__main__":
    try:
        db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        db_instance_details=get_rds_instance_details(db_instance_identifier)
        current_running_version=db_instance_details['EngineVersion']
        Engine=db_instance_details['Engine']
        target_version = target_engine_version
        if check_read_replica_present(db_instance_identifier,replica_db_identifier):
            logger.error(f"Read Replicas already present `{replica_db_identifier}")
            print({
                "output": {
                    "success": "FAILED",
                    "message": "Read Replicas already present",
                },
                "nextStageInput": {"Result": False},
            })
        else:
            logger.info(f"Read Replicas not present `{replica_db_identifier}")
            print({"output": {
                    "success": "Success",
                    "message": "Read Replica not present ",
                },
                "nextStageInput": {"Result": True},
            })

    except Exception as error:
        logger.error(error, exc_info=True)
        print ({
            "output": {
                "success": "FAILED",
                "message": "Caught an exception!",
            },
            "nextStageInput": {"Result": False},
        })
