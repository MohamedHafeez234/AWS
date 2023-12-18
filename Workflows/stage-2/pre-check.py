# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os
import json
workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/rds")
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
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

def handler(input, *args):
    try:
        db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        db_instance_details=get_rds_instance_details(replica_db_identifier)
        Engine_version=db_instance_details['EngineVersion']
        current_running_version=float(Engine_version)
        Engine=db_instance_details['Engine']
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            if check_parameter_group_exist(new_parameter_group_name):
                logger.info(f"Found Parameter Group: `{new_parameter_group_name}")
                if float(current_running_version) < float(target_engine_version) :
                    upgrade_possible=check_target_engine_version(replica_db_identifier,target_engine_version, Engine)
                    if upgrade_possible:
                        logger.info(f"Upgrade to version '{target_engine_version}' is possible.")
                        if check_pending_reboot(replica_db_identifier):
                            if reboot_db_instance_for_parameter_change(replica_db_identifier): #Need to call reboot function
                                while True:
                                    response=wait_until_instance_active(replica_db_identifier)
                                    if response:
                                        return {
                                            "output": {
                                                "success": "SUCCESSFULL",
                                                "message": "Reboot of instance '{replica_db_identifier}' is Done.Pre-checks validated before upgrade.",
                                            },
                                            "nextStageInput": {"Result": True},
                                            }
                        else:
                            return {
                                    "output": {
                                        "success": "SUCCESSFULL",
                                        "message": "Pre-checks validated before upgrade.",
                                    },
                                    "nextStageInput": {"Result": True},
                                    }
                    else:
                        
                        return {
                                "output": {
                                            "success": "FAILED",
                                            "message": "Upgrade to version '{target_engine_version}' is not possible.",
                                            },
                                "nextStageInput": {"Result": False},
                                }
                else:
                    return {
                                "output": {
                                            "success": "FAILED",
                                            "message": "Current Running Version '{replica_db_identifier}' is Higher than Target Version.",
                                            },
                                "nextStageInput": {"Result": False},
                            }

            else:
                return {
                            "output": {
                                        "success": "FAILED",
                                        "message": "Cannot find `{new_parameter_group_name}` Parameter Group",
                                        },
                            "nextStageInput": {"Result": False},
                        }
    except Exception as error:
        logger.error(error, exc_info=True)
        return {
            "output": {
                "success": "FAILED",
                "message": "error : " + str(error),
            },
            "nextStageInput": {"Result": False},
            }
