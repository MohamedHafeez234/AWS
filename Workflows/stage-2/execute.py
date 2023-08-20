# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/")

import json
from common import LoggerSetup

logger = LoggerSetup(loggerName=str(__file__)).getLogger()

from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    upgrade_db,
)

def handler(input, *args):
    try:
        input = json.loads(input)
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            response=upgrade_db(replica_db_identifier,target_engine_version,new_parameter_group_name,region)
            if response == False:
                return {
                    "output": {"success": "FAILED", "error": response},
                    "nextStageInput": {"Result": False},
                }
            else:
                return {
                    "output": {
                        "success": "SUCCESSFUL",
                        "message": "Upgrade was successful",
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


