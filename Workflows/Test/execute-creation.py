import boto3
import time
import logging
import yaml


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

def promote_read_replica(replica_db_identifier):
    try:
        rds_client = boto3.client('rds',region)
        # Step: Promote read replica will detach from Master
        response2 = rds_client.promote_read_replica(
            DBInstanceIdentifier=replica_db_identifier
        )
        time.sleep(30)
        print("Waited for 30secs ")
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=replica_db_identifier)
        response1 = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if response1['DBInstances'][0]['DBInstanceStatus'] == 'available':
            logging.warning("Read replica '{replica_db_identifier}' is available.")
            print(f'True - Promoted replica is now Available')
            return True

    except Exception as e:
        logging.error(f"Error detaching read replica: {e}")
        return None    

def create_read_replica(source_db_identifier,replica_db_identifier):
    try:
        rds_client = boto3.client('rds', region)
        #Step: Creating Read Replicas
        response = rds_client.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_db_identifier,
            SourceDBInstanceIdentifier=source_db_identifier,
            AutoMinorVersionUpgrade=False,
            DeletionProtection=True,
        )
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=replica_db_identifier)
        while True:
            response1 = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
            if response1['DBInstances'][0]['DBInstanceStatus'] == 'available':
                logging.info("Read replica '{replica_db_identifier}' is available.")
                return True
            else:
                time.sleep(5)
                logging.info("Sleep 5 sec")
    except Exception as e:
        logging.error(f"Error creating read replica: {e}")
        return None  
                


if __name__ == "__main__":
    db_instance_identifier= 'test-aws-db'
    replica_db_identifier='test-aws-db-2'
    response=create_read_replica(db_instance_identifier,replica_db_identifier)
    if response:
        promote=promote_read_replica(replica_db_identifier)
        if promote:
            print ({
                "output": {
                    "success": "SUCCESSFUL",
                    "message": "Promotion of Read Replica is successful.",
                },
                "nextStageInput": {"Result": True},
            })
        else:
            print({
                "output": {
                    "success": "FAILED",
                    "message": "Unable to Promote Read Replica.",
                },
                "nextStageInput": {"Result": False},
            })

