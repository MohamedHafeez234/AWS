# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import boto3
import time
import logging
import yaml
import json

def read_yaml(file_path):
    # Read YAML file
    data_loaded=None;
    with open(file_path, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    return data_loaded

region="ap-south-1"
creds_file_path="/Users/mohamed.hafeez.ext/Documents/infra-switch/cred.yaml"
creds = read_yaml(creds_file_path)
boto3 = boto3.Session(
        aws_access_key_id=creds['aws']['aws_access_key_id'],
        aws_secret_access_key=creds['aws']['aws_secret_access_key'],
        aws_session_token=creds['aws']['aws_session_token'],
        profile_name=creds['aws']['profile_name']
        )

def wait_until_instance_active(db_instance_identifier):
        try:
            while True:
                rds_client = boto3.client('rds', region)
                response = rds_client.describe_db_instances(
                    DBInstanceIdentifier=db_instance_identifier
                )
                if 'DBInstances' in response and len(response['DBInstances']) > 0:
                    instance_status = response['DBInstances'][0]['DBInstanceStatus']
                    logging.info(f"Current instance status: {instance_status}")
                    if instance_status == 'available':
                        logging.info(f"Instance is active.")
                        return True
                else:
                    logging.error(f"Instance details not found.")
                time.sleep(10)
        
        except Exception as error:
            logging.error(error, exc_info=True)
            return False

def validate_db_creation(replica_db_identifier):
    try:
        rds_client = boto3.client('rds', region)
        response = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            if instance['DBInstanceStatus'] == 'available':
                if 'DBClusterIdentifier' not in instance:
                    logging.info("Replica Is Standalone")
                    return True  # If DBClusterIdentifier is null , then its Standalone instance
        return False  
    
    except Exception as e:
        logging.error(f"Error validating DB creation: {e}")
        return False

def validate_db():
    try:
        db_instance_identifier,target_engine_version, new_parameter_group_name,replica_db_identifier = ['test-aws-db','13.11','test-aws-13-pg','test-aws-db-2']
        while True:
            response_message=wait_until_instance_active(db_instance_identifier)
            if response_message == True:
                logging.info(f"Instance -  {db_instance_identifier} is Active.")
                break
        while True:
            response_message=wait_until_instance_active(replica_db_identifier)
            if response_message == True:
                logging.info(f"Instance -  {replica_db_identifier} is Active.")
                break
        stage_input = True
        if stage_input:
            response=validate_db_creation(replica_db_identifier)
            if response:
                print({
                    "output": {
                        "success": "SUCCESSFUL",
                        "message": "Read Replica instance is standalone.",
                    },
                    "nextStageInput": {"Result": True},
                })
                return True
            else:
                print({
                    "output": {
                        "success": "IN-PROGRESS",
                        "message": "Read Replica instance is not standalone.",
                    },
                    "nextStageInput": {"Result": False},
                })
                return False


    except Exception as error:
        logging.error(error, exc_info=True)
        print({
            "output": {
                "success": "FAILED",
                "message": "Caught an exception.",
            },
            "nextStageInput": {"Result": False},
        })

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
    response=validate_db()
    #db_instance_identifier,target_engine_version, new_parameter_group_name,replica_db_identifier = ['test-aws-db','13.11','test-aws-13-pg','test-aws-db-2']
    #response1=check_read_replica_present(db_instance_identifier, replica_db_identifier)
    print(response)





