# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/")

import json

from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    get_rds_instance_details,
    check_target_engine_version,
    check_parameter_group_exist,
    check_pending_reboot,
    reboot_db_instance_for_parameter_change,
    wait_until_instance_active,
)

logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()

def handler(input, *args):
    try:
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        db_instance_name = replica_db_identifier
        db_instance_details=get_rds_instance_details(db_instance_name,region)
        current_running_version=db_instance_details['EngineVersion']
        Engine=db_instance_details['Engine']
        target_version = target_engine_version
        stage_input= json.loads(args[0])
        if stage_input["Result"] == True:
            if check_parameter_group_exist(new_parameter_group_name,region):
                logger.info(f"Found Parameter Group: `{new_parameter_group_name}")
            else:
                logger.error(f"Cannot find `{new_parameter_group_name}` Parameter Group")

            if current_running_version < target_version:
                upgrade_possible=check_target_engine_version(db_instance_name,target_engine_version, Engine, region)
                if upgrade_possible:
                    logger.info(f"Upgrade to version '{target_version}' is possible.")
                else:
                    logger.error(f"Upgrade to version '{target_version}' is not possible.")
            
            #execute need to be triggered #result = upgrade_rds_postgres_db(db_instance_name, target_version)
            if check_pending_reboot(db_instance_name,region):
                if reboot_db_instance_for_parameter_change(db_instance_name,region): #Need to call reboot function
                    while True:
                        response=wait_until_instance_active(db_instance_name, region)
                        if response:
                            break
                        logger.info(f"Reboot of instance '{db_instance_name}' is Done.")

            else:
                logger.error(f"Reboot of instance '{db_instance_name}' is not needed.")

        return {
            "output": {
                "success": "SUCCESSFUL",
                "message": "Pre-checks validated before upgrade.",
            },
            "nextStageInput": {"Result": True},
            }

    except Exception as error:
        logger.error(error, exc_info=True)

        return {
            "output": {
                "success": "FAILED",
                "message": "Caught an exception!",
            },
            "nextStageInput": {"Result": False},
            }