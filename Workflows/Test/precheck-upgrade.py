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

def get_rds_instance_details(instance_name):
    try:
        rds_client = boto3.client('rds', region)

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

def check_target_engine_version(replica_db_identifier,target_engine_version, Engine):
    try:
        rds_client = boto3.client('rds',region)
        instance_details = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        current_engine_version = float(instance_details['DBInstances'][0]['EngineVersion'])
        # Get information about the target and current engine versions
        response = rds_client.describe_db_engine_versions(
            Engine=Engine,  # Replace with your engine type (e.g., 'postgres', 'mysql', 'oracle')
            EngineVersion=str(target_engine_version)
        )
        target_version_info= float(response['DBEngineVersions'][0]['EngineVersion'])
        if target_version_info > current_engine_version:
            return True
        else:
            return False
    except Exception as e:
        print("Unable to upgrade to target version:", str(e))
        return None


def check_parameter_group_exist(parameter_group_name):
    try:
        rds_client = boto3.client('rds', region)
        response = rds_client.describe_db_parameter_groups(
            DBParameterGroupName=parameter_group_name
        )
        # If there is at least one parameter group with the specified name, it exists
        return len(response['DBParameterGroups']) > 0
    except Exception as e:
        print(f"Error checking parameter group existence: {e}")
        return False


def reboot_db_instance_for_parameter_change(instance_identifier):
    try:
        rds_client = boto3.client('rds',region)
        response = rds_client.reboot_db_instance(
            DBInstanceIdentifier=instance_identifier
        )
        logger.info(f"Reboot initiated successfully")
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=replica_db_identifier)
        return True

    except Exception as e:
        logger.error(f"Error rebooting RDS instance: {e}")
        return False

def wait_until_instance_active(instance_identifier,region):
        try:
            while True:
                rds_client = boto3.client('rds', region)
                response = rds_client.describe_db_instances(
                    DBInstanceIdentifier=instance_identifier
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

def check_pending_reboot(replica_db_identifier):
    try:
        rds_client = boto3.client('rds', region)
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=replica_db_identifier
        )
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            if instance['DBParameterGroups'][0]['ParameterApplyStatus'] != 'in-sync':
                logger.info("Parameter changes require a reboot.")
                return True
            else:
                logger.info("No pending reboot required.")
                return False
        else:
            logger.info("Instance not found")
            return False

    except Exception as e:
        return False, f"Error checking pending reboot: {e}"


if __name__ == "__main__":
    try:
        db_instance_identifier,target_engine_version , new_parameter_group_name,replica_db_identifier = ['test-aws-db',14.4,'test-sre-db-13','test-aws-db-2']
        db_instance_details=get_rds_instance_details(replica_db_identifier)
        Engine_version=db_instance_details['EngineVersion']
        current_running_version=float(Engine_version)
        Engine=db_instance_details['Engine']
        stage_input= True
        if stage_input == True:
            if check_parameter_group_exist(new_parameter_group_name):
                logger.info(f"Found Parameter Group: `{new_parameter_group_name}")
                if float(current_running_version) < float(target_engine_version) :
                    upgrade_possible=check_target_engine_version(replica_db_identifier,target_engine_version, Engine)
                    if upgrade_possible:
                        logger.info(f"Upgrade to version '{target_engine_version}' is possible.")
                        if check_pending_reboot(replica_db_identifier):
                            if reboot_db_instance_for_parameter_change(replica_db_identifier): #Need to call reboot function
                                while True:
                                    response=wait_until_instance_active(replica_db_identifier, region)
                                    if response:
                                        print( {
                                            "output": {
                                                "success": "SUCCESSFUL",
                                                "message": "Pre-checks validated before upgrade.",
                                            },
                                            "nextStageInput": {"Result": True},
                                            })
                                        break
                                    logger.info(f"Reboot of instance '{replica_db_identifier}' is Done.")
                        else:
                            print({
                                    "output": {
                                        "success": "SUCCESSFUL",
                                        "message": "Pre-checks validated before upgrade.",
                                    },
                                    "nextStageInput": {"Result": True},
                                    })
                    else:
                        logger.error(f"Upgrade to version '{target_engine_version}' is not possible.")
                        print({
                                "output": {
                                            "success": "Failed",
                                            "message": "Pre-checks Failed before upgrade.",
                                            },
                                "nextStageInput": {"Result": False},
                                            })
                else:
                    logger.error(f"Current Running Version '{replica_db_identifier}' is Higher than Target Version.")
                    print( {
                                "output": {
                                            "success": "Failed",
                                            "message": "Pre-checks Failed before upgrade.",
                                            },
                                "nextStageInput": {"Result": False},
                                            })

            else:
                logger.error(f"Cannot find `{new_parameter_group_name}` Parameter Group")
                print( {
                            "output": {
                                        "success": "Failed",
                                        "message": "Pre-checks Failed before upgrade.",
                                        },
                            "nextStageInput": {"Result": False},
                                        })
        

    except Exception as error:
        logger.error(error, exc_info=True)

        print( {
            "output": {
                "success": "FAILED",
                "message": "Caught an exception!",
            },
            "nextStageInput": {"Result": False},
            })
