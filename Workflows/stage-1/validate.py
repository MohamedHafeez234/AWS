# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/rds")
import json
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    wait_until_instance_active,
    validate_db_creation,
    )

def handler(input, *args):
    try:
        db_instance_identifier,region,target_engine_version,new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        stage_input = json.loads(args[0])
        while True:
            response_message=wait_until_instance_active(db_instance_identifier)
            if response_message == True:
                logger.info(f"Instance -  {db_instance_identifier} is Active.")
                break
        while True:
            response_message1=wait_until_instance_active(replica_db_identifier)
            if response_message1 == True:
                logger.info(f"Instance -  {replica_db_identifier} is Active.")
                break
        if stage_input["Result"] == True:
                response=validate_db_creation(replica_db_identifier)
                if response:
                    return{
                        "output": {
                            "success": "SUCCESSFULL",
                            "message": "Read Replica instance is standalone.",
                        },
                        "nextStageInput": {"Result": True},
                    }
                    
                else:
                    return{
                        "output": {
                            "success": "INPROGRESS",
                            "message": "Read Replica instance is not standalone.",
                        },
                        "nextStageInput": {"Result": False},
                    }

    except Exception as error:
        logger.error(error, exc_info=True)
        return{
            "output": {
                "success": "FAILED",
                "message": "error : " + str(error),
            },
            "nextStageInput": {"Result": False},
        }
