# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/")

import json

from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    get_rds_instance_details,
    is_max_replicas_reached,
    check_read_replica_present,
)

logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()

def handler(input, *args):
    try:
        input = json.loads(input)
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        db_instance_name = db_instance_identifier
        db_instance_details=get_rds_instance_details(db_instance_name,region)
        current_running_version=db_instance_details['EngineVersion']
        Engine=db_instance_details['Engine']
        target_version = target_engine_version
        if is_max_replicas_reached(db_instance_name,region):
            logger.info(f"Max Replicas count reached `{db_instance_name}")
            if check_read_replica_present(db_instance_identifier,replica_db_identifier, region):
                logger.error(f"Read Replicas already present `{replica_db_identifier}")
                return {
                    "output": {
                        "success": "FAILED",
                        "message": "Read Replicas already present",
                    },
                    "nextStageInput": {"Result": False},
                }
            else:
                logger.info(f"Read Replicas not present `{replica_db_identifier}")
                return {"output": {
                        "success": "Success",
                        "message": "Read Replica not working ",
                    },
                    "nextStageInput": {"Result": True},
                }
        
        else:
            logger.error(f"Max Replicas count reached `{db_instance_name}")
            return {
                    "output": {
                        "success": "FAILED",
                        "message": "Max Replicas count reached",
                    },
                    "nextStageInput": {"Result": False},
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