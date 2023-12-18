import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/rds")
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    get_rds_instance_details,
    check_read_replica_present,
)

def handler(input, *args):
    try:
        db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
        db_instance_details=get_rds_instance_details(db_instance_identifier)
        current_running_version=db_instance_details['EngineVersion']
        Engine=db_instance_details['Engine']
        target_version = target_engine_version
        if check_read_replica_present(db_instance_identifier,replica_db_identifier):
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
            return {
                "output": {
                    "success": "SUCCESSFULL",
                    "message": "Read Replica not present `{replica_db_identifier}` ",
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
