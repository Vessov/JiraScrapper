# Error Codes

## Main Script errors - 1XXX

*Errors encountered during executions of strictly main script - in this case `JiraScrapper.py`*


## Structures errors - 2XXX

*Errors encoutered during instantiation of Project/Issue classes, or when calling their methods.*

|Error Code | Function | Description |
|:---------:| :--------| :-----------|
| 2101 | `__init__()` | Couldn't associate any developer with the project |
| 2102 | `__init__()` | Project key not found in the config file |
| 2103 | `__init__()` | Couldn't associate any name with the project |
| 2201 | `gather_issues()` | **TBD** |
| 2301 | `_get_parent()` | JIRAException when looking for parent issue |
| 2401 | `_get_channel()` | Unable to establish SuperEpic and distribution channel <br> due to lack of epic |
| 2402 | `_get_channel()` | Parent Epic of the specific issue does not have <br> correct link to any SuperEpic |
| 2403 | `_get_channel()` | Unable to find SuperEpic and distribution channel <br> for the specific issue |
| 2501 | `_get_tester()` | Unable to find tester associated with the specific issue |





## Database handler errors - 3XXX
  
*Errors encountered during communication with MySQL database, inputting data in it, etc., mainly by `DBHandler.py`*

|Error Code | Function | Description |
|:---------:| :--------| :-----------|
| 3201 | `_establish_connection()` | Can't correctly connect to database
| 3301 | `_check_tables()` | Not all needed tables are present in the database
| 3401 | `_check_issue_existence()` | More than one issue with this exact key <br> exists in the database |
| 3501 | `get_singe_issue_info()` | **TBD** |
| 3601 | `get_all_project_issues_info()` | No issues with the selected project prefix <br> were found |
| 3602 | `get_all_project_issues_info()` | No issues with the selected project ID were found |
| 3603 | `get_all_project_issues_info()` | Incorrect or no project prefix/ID |


## Jira handler errors - 4XXX

*Errors encountered while communicating with Jira - mainly during data collection - by `JiraHandler.py`*

|Error Code | Function | Description |
|:---------:| :--------| :-----------|
| 4201 | `_establish_connection()` | Incorrect authentication, HTTP status code 401 |
| 4202 | `_establish_connection()` | Incorrect server address, HTTP status code 404 |
| 4203 | `_establish_connection()` | Connection error, for details check log |



## Setup/repair errors - 9XXX

*Errors encountered while setting up architecture or while using backup/init functions during auto-repair; mainly from `Setup.py` and all utility tools with `backup` and `init` in names.*




