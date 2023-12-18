# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/rds")
import json
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    upgrade_db,
)

def handler(input, *args):
    try:
        db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            response=upgrade_db(replica_db_identifier,target_engine_version,new_parameter_group_name)
            if response == False:
                return {
                    "output": {
                        "success": "FAILED", 
                        "message": "Upgrade of Instance Failed '{replica_db_identifier}'"},
                    "nextStageInput": {"Result": False},
                }
            else:
                return {
                    "output": {
                        "success": "SUCCESSFULL",
                        "message": "Upgrade was successful",
                    },
                    "nextStageInput": {"Result": True},
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

