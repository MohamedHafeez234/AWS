# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/")

import json

from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    wait_until_instance_active,
    validate_db_creation,
    )
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()

def handler(input, *args):
    try:
        input = json.loads(input)
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        while True:
            response_message=wait_until_instance_active(db_instance_identifier,region,sleep_interval=10)
            if response_message == True:
                logger.info(f"Instance -  {db_instance_identifier} is Active.")
                break
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            response=validate_db_creation(replica_db_identifier,region)
            if response:
                return {
                    "output": {
                        "success": "SUCCESSFUL",
                        "message": "Read Replica instance is standalone.",
                    },
                    "nextStageInput": {"Result": True},
                }
            else:
                return {
                    "output": {
                        "success": "Failed",
                        "message": "Read Replica instance is not standalone.",
                    },
                    "nextStageInput": {"Result": False},
                }


    except Exception as error:
        logger.error(error, exc_info=True)
        return {
            "output": {
                "success": "FAILED",
                "message": "Caught an exception.",
            },
            "nextStageInput": {"Result": False},
        }




