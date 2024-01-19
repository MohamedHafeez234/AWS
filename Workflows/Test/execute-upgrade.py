# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os
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
    "target_engine_version": "11.20",
    "new_parameter_group_name": "test-sre-db-11",
    "Replica_DB_Identifier": "test-aws-db-2",
    "DNS_Record_Name": "db1.juspay.local",
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


def upgrade_db(replica_db_identifier,target_version,new_parameter_group_name):
    try:
        rds_client = boto3.client('rds', region)
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=replica_db_identifier,
            EngineVersion=str(target_version),
            AllowMajorVersionUpgrade=True,
            DBParameterGroupName=new_parameter_group_name,
            AutoMinorVersionUpgrade=True,
            ApplyImmediately=True,
        )
        logger.info("Upgrading the DB Engine")
        time.sleep(15)
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=replica_db_identifier)
        while True:
            response1 = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
            if response1['DBInstances'][0]['DBInstanceStatus'] == 'available':
                logger.debug("Read replica '{replica_db_identifier}' is available.")
                return True
            else:
                time.sleep(5)
                logger.info("sleep 5 sec")

    except Exception as e:
        logger.error(f"Error upgrading the DB: {e}")
        return False

if __name__ == "__main__":
    try:
        db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        stage_input = True
        if stage_input == True:
            response=upgrade_db(replica_db_identifier,target_engine_version,new_parameter_group_name)
            if response == False:
                print({
                    "output": {"success": "FAILED", 
                    "message": response
                    },
                    "nextStageInput": {"Result": False},
                })
            else:
                print( {
                    "output": {
                        "success": "SUCCESSFUL",
                        "message": "Upgrade was successful",
                    },
                    "nextStageInput": {"Result": True},
                })

    except Exception as error:
        logger.error(error, exc_info=True)

        print({
            "output": {
                "success": "FAILED",
                "message": error,
            },
            "nextStageInput": {"Result": False},
        })


