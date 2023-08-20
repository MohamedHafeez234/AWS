import boto3
import json

rds_client = boto3.client('rds', region_name='ap-south-1')

# Function for getting rds instance detail for which upgrade is needed
def get_rds_instance_details(instance_name):
    try:
        # Get all RDS instances in the AWS account
        response = rds_client.describe_db_instances()

        # Find the instance with the specified name
        for instance in response['DBInstances']:
            if instance['DBInstanceIdentifier'] == instance_name:
                return instance
        # If the instance is not found, return None
        return None

    except Exception as e:
        print("Error occurred while getting RDS instance details:", str(e))
        return None

## Creation of RDS Snapshot 
def create_rds_snapshot(instance_identifier, snapshot_identifier):
    try:
        # Create the manual snapshot
        response = rds_client.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_identifier,
            DBInstanceIdentifier=instance_identifier
        )
        return response
    except Exception as e:
        print("Error Taking Manual Snapshot", str(e))
        return None

# Creation of Parameter Group
def create_parameter_group(parameter_group_name, family, description):
    try:
        response = rds_client.create_db_parameter_group(
            DBParameterGroupName=parameter_group_name,
            DBParameterGroupFamily=family,
            Description=description
        )
        print("Parameter group created successfully.")
        return response['DBParameterGroup']
    except Exception as e:
        print(f"Error creating parameter group: {e}")
        return None

# Function for checking whether reboot is needed / not for the parameter value change 
def is_reboot_needed(parameter_group_name, parameter_name, parameter_value):
    try:
        response = rds_client.describe_db_parameters(
            DBParameterGroupName=parameter_group_name,
            Filters=[
                {
                    'Name': 'name',
                    'Values': [parameter_name]
                }
            ]
        )

        # If the parameter exists and has a different value, a reboot is needed
        for param in response['Parameters']:
            if param['ParameterName'] == parameter_name and param['ParameterValue'] != parameter_value:
                return True

        return False
    except Exception as e:
        print(f"Error checking reboot status: {e}")
        return None

## function for altering the parameter groups / Also checks for reboot is needed or not 
def alter_parameter_in_group(parameter_group_name, parameter_name, parameter_value):
    try:
        reboot_needed = is_reboot_needed(parameter_group_name, parameter_name, parameter_value)
        if reboot_needed:
            print("A reboot is needed to apply the parameter changes.")
        else:
            print("No reboot is needed. The parameter changes will take effect immediately.")
            response = rds_client.modify_db_parameter_group(
                DBParameterGroupName=parameter_group_name,
                Parameters=[
                    {
                        'ParameterName': parameter_name,
                        'ParameterValue': parameter_value,
                        'ApplyMethod': 'immediate'
                    },
                ]
            )
            print("Parameter altered successfully.")
        return response
    except Exception as e:
        print(f"Error altering parameter: {e}")
        return None

## Create a read replica and detach the instance from Master 
def create_and_detach_read_replica(source_db_identifier, replica_db_identifier, availability_zone=None):
    try:
        # Step 1: Create the read replica
        response = rds_client.create_db_instance_read_replica(
            DBInstanceIdentifier=replica_db_identifier,
            SourceDBInstanceIdentifier=source_db_identifier,
            AvailabilityZone=availability_zone,
        )
        print("Read replica creation initiated successfully.")

        # Step 2: Detach read replica from the master (set Multi-AZ attribute to False) / Minor upgrade disabling / Deletion protection enabling
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=replica_db_identifier,
            MultiAZ=False,
            AutoMinorVersionUpgrade=False,
            DeletionProtection=True,
        )
        print("Read replica detached from the master.")
        return response['DBInstance']
    except Exception as e:
        print(f"Error creating or detaching read replica: {e}")
        return None


def upgrade_rds_postgres_db(db_instance_identifier, target_engine_version):
    """
    Automates the upgrade of a PostgreSQL database in AWS RDS.

    Parameters:
        db_instance_identifier (str): The identifier of the RDS instance (DB instance name).
        target_engine_version (str): The target PostgreSQL engine version for the upgrade (e.g., '12.7', '13.4', etc.).

    Returns:
        dict: A dictionary containing the response from the RDS modify_db_instance API call.
    """
    try:
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            EngineVersion=target_engine_version,
            ApplyImmediately=True,
        )
        return response
    except Exception as e:
        return {
            'error': str(e)
        }

def main():

## For Fetching the RDS Details of the Instance mentioned
    instance_name = "your_rds_instance_name"  ## Getting Input RDS Instance name 
    instance_details = get_rds_instance_details(instance_name)
    if instance_details:
        print("RDS Instance Details:")
        print("Instance Identifier:", instance_details['DBInstanceIdentifier'])
        print("Instance Class:", instance_details['DBInstanceClass'])
        print("DB Parameter Group Name:", instance_details['DBParameterGroups'][0]['DBParameterGroupName'])
        print("Engine Version:", instance_details['EngineVersion'])
        # Add more fields as needed based on your requirement
    else:
        print(f"RDS instance '{instance_name}' not found.")

# For creation of parameter group for new version

    parameter_group_name = 'your_parameter_group_name_here'  # Input from user 
    family = 'postgres13'  # Change this to the appropriate parameter group family for your database engine
    description = 'Your parameter group description here'  # Input from user / anything dump 

    created_parameter_group = create_parameter_group(parameter_group_name, family, description)

    if created_parameter_group:
        # Example to alter a parameter in the created parameter group:
        parameter_name = 'parameter_name_to_alter_here'  # Need to input / default
        parameter_value = 'new_parameter_value_here'     # Need to change for which value

        changed_parameter_group = alter_parameter_in_group(parameter_group_name, parameter_name, parameter_value)

# Need to use the changed_parameter_group for the new instance launch

# Creating a new read replica and detach from the Master 
    source_db_identifier = instance_name
    replica_db_identifier = 'your_new_dbname_instance_here' # Need to Input
    availability_zone = None  # Optional, specify if desired

    replica_instance = create_and_detach_read_replica(source_db_identifier, replica_db_identifier, availability_zone)
    if replica_instance:
        print(f"Read replica '{replica_instance['DBInstanceIdentifier']}' created and configured.")

# For Creating the snapshot 
    snapshot_id = "your_snapshot_identifier"    ##need to input snapshot name
    snapshot_info = create_rds_snapshot(instance_name, snapshot_id)
    if snapshot_info:
        print("Snapshot created successfully:", snapshot_info['DBSnapshot']['DBSnapshotIdentifier'])
        db_instance_name = replica_instance
        current_running_version=instance_details['EngineVersion']
        target_version = '13.4'   ## need to input from user 
        if current_running_version < target_version:
            result = upgrade_rds_postgres_db(db_instance_name, target_version)
            if 'error' in result:
                print(f"Error occurred: {result['error']}")
            else:
                print("Upgrade initiated successfully.")
        else:
            print("Current Version is already above mentioned version")

if __name__ == "__main__":
   main()