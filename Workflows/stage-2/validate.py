# Facing issue with importing common package, added the current execution path(python3 stage-1/pre-check.py) to sys.path
import sys, os

workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.append(workflow_script_path + "database/rds")
logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
import json
from common.logger import LoggerSetup
from common.utilities import (
    getinput,
    wait_until_instance_active,
    validate_db_upgrade,
    check_route53_for_rds_dns,
    )

def handler(input, *args):
    try:
        db_instance_identifier, region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name = getinput(input)
        stage_input = json.loads(args[0])
        if stage_input["Result"] == True:
            while True:
                response=wait_until_instance_active(replica_db_identifier)
                if response:
                    logger.info(f"Instance -  {replica_db_identifier} is Active.")
                    response=validate_db_upgrade(replica_db_identifier,target_engine_version)
                    if response == target_engine_version:
                        response2=check_route53_for_rds_dns(dns_record_name,db_instance_identifier,replica_db_identifier)
                        if response2 == True:
                            logger.info("The RDS Endpoint is flipped")
                            return {
                            "output": {
                                "success": "SUCCESSFULL",
                                "message": "Healthy Instance Post Upgrade and DNS flipped Successfully",
                            },
                            "nextStageInput": {"Result": True},
                            }
                        elif response2 == "In-progress":
                            logger.info("The RDS Endpoint is not flipped yet")
                            return {
                            "output": {
                                "success": "INPROGRESS",
                                "message": "Upgrade is Successful and DNS is not flipped yet.",
                            },
                            "nextStageInput": {},
                            }
                    else:
                        return {
                            "output": {
                                "success": "FAILED",
                                "message": "Upgrade to Target version was unsuccessful.",
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
