import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/")

import json
import boto3
from common import LoggerSetup

logger = LoggerSetup(loggerName=str(__file__)).getLogger()

from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    create_read_replica,
    promote_read_replica
)

def handler(input, *args):
    try:
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier = getinput(input)
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            response=create_read_replica(db_instance_identifier,replica_db_identifier,region)
            if response:
                promote=promote_read_replica(replica_db_identifier,region)
                if promote:
                    return {
                        "output": {
                            "success": "SUCCESSFUL",
                            "message": "Promotion of Read Replica is successful.",
                        },
                        "nextStageInput": {"Result": True},
                    }
                else:
                    return {
                        "output": {
                            "success": "FAILED",
                            "message": "Unable to Promote Read Replica.",
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



