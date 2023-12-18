#!/usr/bin/python3
import boto3
import json
import time

logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
from common.logger import LoggerSetup

def getinput(input):
    try:
        context = json.loads(input)
        db_instance_identifier = context.get("db_instance_identifier")
        region = context.get("metadata").get("region")
        target_engine_version = context.get("target_engine_version")
        new_parameter_group_name = context.get("metadata").get("new_parameter_group_name")
        replica_db_identifier=input.get("Replica_DB_Identifier")
        dns_record_name= context.get("DNS_Record_Name")
    except Exception as e:
        logger.error("There's an issue with input: " + str(e))
    return [db_instance_identifier, region, target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name]

def get_rds_instance_details(instance_name,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        # Get all RDS instances in the AWS account
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_name)
        # Find the instance with the specified name
        for instance in response['DBInstances']:
            if instance['DBInstanceIdentifier'] == instance_name:
                return instance
        # If the instance is not found, return None
        return None

    except Exception as e:
        logger.error("Error occurred while getting RDS instance details:", str(e))
        return None

def get_parameter_list(db_identifier=None,parameter_group_identifier=None):
    try:
        Parameters={}
        rds_client = boto3.client('rds')
        
        if db_identifier is not None :
            rds_instance_parameter_group = rds_client.describe_db_instances(
                DBInstanceIdentifier=db_identifier
            )['DBInstances'][0]['DBParameterGroups'][0]['DBParameterGroupName']
        elif parameter_group_identifier is not None :
            rds_instance_parameter_group=parameter_group_identifier

        parameter_group_describe = rds_client.get_paginator('describe_db_parameters')
        list_parameters = parameter_group_describe.paginate(DBParameterGroupName=rds_instance_parameter_group)
        for i in list_parameters:
            for j in i['Parameters']:
                try:
                    Parameters[j['ParameterName']]=j['ParameterValue']
                except:
                    pass
        if db_identifier is not None :
            logger.info(f"The Parameter list for the given {db_identifier} is {Parameters}")
        elif parameter_group_identifier is not None :
            logger.info(f"The Parameter list for the given {parameter_group_identifier} is {Parameters}")
        return Parameters
  
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def display_parameter_group_differences(old_db_parameters,new_db_parameters):
    try:
        rds_client = boto3.client('rds')
        all_keys = set(old_db_parameters.keys()) | set(new_db_parameters.keys())
        old=[]
        new=[]
        diff=[]
        for key in all_keys:
            A = old_db_parameters.get(key)
            B = new_db_parameters.get(key)
            if A == None and B != None:
                new.append([key,B])
            elif A != None and B == None:
                old.append([key,A])
            elif A != B:
                diff.append([key,B,A])
        logger.info(f"Parameters Present in only Old DB are {old}")
        logger.info(f"Parameters Present in only New DB are {new}")
        logger.info(f"Parameters Present in both the DB's with different values are {diff}")
        return [old,new,diff]
    except Exception as e:
        logger.error(f"Error: {str(e)}")

def check_target_engine_version(instance_detail,target_engine_version, Engine,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        current_engine_version = instance_detail['DBInstances'][0]['EngineVersion']
        response = rds_client.describe_db_engine_versions(
            Engine,
            EngineVersion=target_engine_version
        )
        target_version_info = response['DBEngineVersions'][0]
        if target_version_info['EngineVersion'] > current_engine_version:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Unable to upgrade to target version:", str(e))
        return None

def check_parameter_group_exist(parameter_group_name,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        response = rds_client.describe_db_parameter_groups(
            DBParameterGroupName=parameter_group_name
        )
        # If there is at least one parameter group with the specified name, it exists
        return len(response['DBParameterGroups']) > 0
    except Exception as e:
        logger.error(f"Error checking parameter group existence: {e}")
        return False


def check_pending_reboot(instance_identifier,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=instance_identifier
        )

        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]

            if 'PendingModifiedValues' in instance:
                pending_values = instance['PendingModifiedValues']

                if 'ParameterApplyStatus' in pending_values and pending_values['ParameterApplyStatus'] == 'pending-reboot':
                    return True, f"Parameter changes require a reboot."
                else:
                    return False, f"No pending reboot required."
            else:
                return False, f"No pending modifications."
        else:
            return False, f"Instance not found."

    except Exception as e:
        return False, f"Error checking pending reboot: {e}"

def reboot_db_instance_for_parameter_change(instance_identifier,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        response = rds_client.reboot_db_instance(
            DBInstanceIdentifier=instance_identifier
        )
        logger.info(f"Reboot initiated successfully")
        return True

    except Exception as e:
        logger.error(f"Error rebooting RDS instance: {e}")
        return False

def wait_until_instance_active(instance_identifier):
        try:
            while True:
                rds_client = boto3.client('rds')
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
                    return False
                
                time.sleep(10)
        
        except Exception as error:
            logger.error(error, exc_info=True)
            return False

def is_max_replicas_reached(instance_identifier,region):
    try:
        rds_client = boto3.client('rds', region_name=region)
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=instance_identifier
        )

        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]

            current_replica_count = instance['ReadReplicaDBInstanceIdentifiers']
            max_replicas = instance['ReadReplicaSourceDBInstanceIdentifier']
            if len(current_replica_count) < max_replicas:
                return True
            else:
                return False
        else:
            logger.error(f"DB Instance not found.")
            return False

    except Exception as e:
        logger.error(f"Error checking max replicas: {e}")
        return False

def check_read_replica_present(source_db_identifier, read_replica_identifier):
    try:
        rds_client = boto3.client('rds')
        source_response = rds_client.describe_db_instances(DBInstanceIdentifier=source_db_identifier)
        
        if 'DBInstances' in source_response:
            source_instance = source_response['DBInstances'][0]
            if 'ReadReplicaDBInstanceIdentifiers' in source_instance:
                replica_identifiers = source_instance['ReadReplicaDBInstanceIdentifiers']
                if read_replica_identifier in replica_identifiers:
                    return True
            else:
                return False
        else:
            return False
        
    except Exception as e:
        logger.error(f"Error checking read replica presence: {e}")
        return False

def create_read_replica(source_db_identifier,replica_db_identifier):
    try:
        rds_client = boto3.client('rds')
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
                logger.info(f"Read replica '{replica_db_identifier}' is available.")
                return True
            else:
                time.sleep(5)

    except Exception as e:
        logger.error(f"Error creating read replica: {e}")
        return None  

def promote_read_replica(replica_db_identifier):
    try:
        rds_client = boto3.client('rds')
        # Step: Promote read replica will detach from Master
        response2 = rds_client.promote_read_replica(
            DBInstanceIdentifier=replica_db_identifier
        )
        time.sleep(15)
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=replica_db_identifier)
        response1 = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if response1['DBInstances'][0]['DBInstanceStatus'] == 'available':
            logger.info(f"Read replica '{replica_db_identifier}' is promoted.")
            return True

    except Exception as e:
        logger.error(f"Error detaching read replica: {e}")
        return None 

def validate_db_creation(replica_db_identifier):
    try:
        rds_client = boto3.client('rds')
        response = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            if instance['DBInstanceStatus'] == 'available':
                if 'DBClusterIdentifier' not in instance:
                    logger.info("Replica Is Standalone")
                    return True  # If DBClusterIdentifier is null , then its Standalone instance
        return False  
    
    except Exception as e:
        logger.error(f"Error validating DB creation: {e}")
        return False

def upgrade_db(replica_db_identifier,target_version,new_parameter_group_name):
    try:
        rds_client = boto3.client('rds')
        response = rds_client.modify_db_instance(
            DBInstanceIdentifier=replica_db_identifier,
            EngineVersion=target_version,
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
                logger.info(f"Read replica '{replica_db_identifier}' is available.")
                return True
            else:
                time.sleep(5)

    except Exception as e:
        logger.error(f"Error upgrading the DB: {e}")
        return False

def validate_db_upgrade(rds_client, replica_db_identifier, target_engine_version):
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=replica_db_identifier)
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            if 'EngineVersion' in instance:
                if instance['EngineVersion'] == target_engine_version:
                    return instance['EngineVersion']
            else:
                return None
        else:
            return None
        
        return False  
    except Exception as e:
        logger.error(f"Error validating DB upgrade: {e}")
        return False

def get_rds_endpoint(instance_identifier):
    try:
        rds_client = boto3.client('rds')
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_identifier)
        
        if 'DBInstances' in response and len(response['DBInstances']) > 0:
            instance = response['DBInstances'][0]
            endpoint = instance.get('Endpoint', {}).get('Address')
            return endpoint
        else:
            logger.info(f"Instance '{instance_identifier}' not found.")
            return None

    except Exception as e:
        logger.error(f"Error getting RDS endpoint: {e}")
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
                if rds_dns == record_set['ResourceRecords'][0]['Value']:
                    #record_set['Name'] = record_name 
                    logger.info(f"The Route 53 record value matches the RDS endpoint DNS.")
                    return "In-progress"
                elif rds_new_dns == record_set['ResourceRecords'][0]['Value']:
                    logger.info(f"The Route 53 record matches the New RDS endpoint DNS.")
                    return True

        logger.info(f"No matching record found for the record for RDS Endpoint.")
        return False
    except Exception as e:
        logger.error(f"Error checking Route 53 for RDS DNS: {e}")
        return False
