import sys, os
import boto3,json
from common.logger import LoggerSetup

logger = LoggerSetup(loggerName=str(__file__), loggingLevel="debug").getLogger()
workflow_script_path = os.getenv("WORKER_SCRIPT_PATH", "workflow-scripts/")
sys.path.insert(0, workflow_script_path + "database/rds/")

from common.utilities import (
    getinput,
    display_parameter_group_differences,
    get_parameter_list,
)
def handler(input, *args):
    try:
        try:
            db_instance_identifier,region,target_engine_version, new_parameter_group_name,replica_db_identifier,dns_record_name= getinput(input)
            old_db_name = db_instance_identifier
            new_db_parameter_group_name = new_parameter_group_name
        except Exception as e:
            logger.error("There's an issue with input: " + str(e))

        old_db_parameters=get_parameter_list(db_identifier=old_db_name)
        if old_db_parameters :
            logger.info(f"Successfully got the parameter list for {input['parameter_group']['old_db_name']} ")
        else:
            logger.error("Unable to get the parameter list for old db")
            raise Exception
        
        new_db_parameters=get_parameter_list(parameter_group_identifier=new_db_parameter_group_name)
        if new_db_parameters :
            logger.info(f"Successfully got the parameter list for {input['parameter_group']['new_db_name']} ")
        else:
            logger.error("Unable to get the parameter list for new db")
            raise Exception
        
        parameter_diff=display_parameter_group_differences(old_db_parameters,new_db_parameters)
        if parameter_diff:
            logger.info("Successfully got the parameter differences between the two Db's")
            return parameter_diff
        else:
            logger.error("Unable to fetch the parameter differences between the two Db's")
            raise Exception
            
    except Exception as error:
        logger.error(error, exc_info=True)

        return {
            "output": {
                "success": "FAILED",
                "message": "Caught an exception!",
            },
            "nextStageInput": {},
        }
