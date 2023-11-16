import os
import yaml
import keyring as kr
import mysql.connector
from typing import Protocol
from enum import Enum


class Logger(Protocol):
    def log(self, message:str, level:str):
        pass


class DBHandler:
    errors = {}

    def __init__(self, logger:Logger, rdir) -> None:
        self._root_dir = rdir
        self.l = logger
        self.db_namespace = "DB"

        self.l.log("Initializing DataBase Connector class", "DEBUG")

        def check_main_errors_dict():
            check_main = self.errors.get('main')
            if check_main is None:
                self.errors['main'] = []

        config_file = os.path.join(rdir, "settings", "config.yaml")

        with open(config_file, 'r') as file:
            config = yaml.load(file, yaml.SafeLoader)
            credentials:dict = config['credentials']
            db_creds:dict = credentials['database']
            host = db_creds['host']
            user = db_creds['user']
            password = db_creds['password']
            database = db_creds['database']

            self.tables:set = set(config['tables'])

        self.connector = self._establish_connection(host, user, password, database)
        if self.connector is not None:
            self.cursor = self.connector.cursor()
            self._check_tables()
    
    def _establish_connection(self, host, user, password, database) -> mysql.connector.MySQLConnection:
        self.l.log("Establishing connection", "DEBUG")

        try:
            mysql_db = mysql.connector.connect(
                host = host,
                user = kr.get_password(self.db_namespace, user),
                password = kr.get_password(self.db_namespace, password),
                database = kr.get_password(self.db_namespace, database)
            )
            self.l.log("Connection correctly established", "DEBUG")
            return mysql_db
        
        except mysql.connector.errors.ProgrammingError as perr:
            self.errors["connection"] = 3201
            self.l.log("Connection not achieved", "ERROR")
            self.l.log(f"Error message: '{perr}'")
            return None
    
    def _check_tables(self):
        self.l.log("Checking if correct tables exist", "DEBUG")

        self.cursor.execute("SHOW TABLES")

        found_tables = set()
        for out_tuple in self.cursor:
            found_tables.add(out_tuple[0])

        self.tables -= found_tables
        
        if len(self.tables) == 0:
            self.l.log("All necessary tables present", "DEBUG")
            return True
        else:
            self.errors["tables"] = 3301
            self.l.log(f"Tables {self.tables} not present!", "ERROR")
            return False

    def _add_error(self, issueKey:str, errorCode):
        
        if self.errors.get(issueKey) is None:
            self.errors[issueKey] = []
        if errorCode not in self.errors[issueKey]:
            self.errors[issueKey].append(errorCode)

    def _check_issue_existence(self, issue_key) -> dict:
        query = f'''SELECT COUNT(1) FROM issues WHERE TestKey=%s
                                UNION
                                SELECT TestKey FROM issues WHERE TestKey=%s'''
        self.cursor.execute(query, (issue_key, issue_key))

        query_return = []
        result = {}
        for x in self.cursor:
            query_return.append(*x)

        if int(query_return[0]) == 1:
            result["found"] = True
            result["key"] = query_return[1]
        elif int(query_return[0]) > 1:
            result["found"] = True
            result["key"] = query_return[1]
            self._add_error(query_return[1], 3401)

        else:
            result["found"] = False
            result["key"] = None
        
        return result

    def get_single_issue_info(self, issueKey):
        self.l.log(f"Starting to gather info of issue {issueKey} from database", "DEBUG")
        exists = self._check_issue_existence(issueKey)
        query = f'''SELECT * FROM issues WHERE TestKey=%s LIMIT 0, 1'''

        if exists.get("found") == True:
            self.l.log(f"Issue {issueKey} found in the database", "RUN")
            self.cursor.execute(query, (issueKey,))
            result = self.cursor.fetchone()
            result_dict = {
                'id': result[0],
                'key': result[1],
                'type': result[2],
                'channel': result[3],
                'testerID': result[4],
                'projectID': result[5],
                'time': result[6],
                'softwareVersion': result[7]
            }
            return result_dict
        
        else:
            self.l.log(f"Issue {issueKey} not found in the database", "RUN")
            return None

    def get_all_project_issues_info(self, project_key:str=None, project_id:int=None):
        self.l.log(f"Starting to gather all issues of project (key:{project_key}, id:{project_id}) from database", "DEBUG")
        return_list = []

        if project_key is not None:
            query = f'''SELECT * FROM issues WHERE INSTR(TestKey, %s) > 0'''
            self.cursor.execute(query, (project_key,))
            result_list:list = self.cursor.fetchall()
            if len(result_list) < 1:
                self.l.log(f"No issues found for project key:{project_key}", "ERROR")
                self._add_error(project_key, 3601)
                return None

        elif project_id is not None:
            query = f'''SELECT * FROM issues WHERE ProjectID = %s'''
            self.cursor.execute(query, (project_id, ))
            result_list:list = self.cursor.fetchall()
            if len(result_list) < 1:
                self.l.log(f"No issues found for project id:{project_id}", "ERROR")
                self._add_error(project_id, 3602)
                return None

        else:
            self.l.log(f"No project with key:{project_key}/id:{project_id} found in the database", "CRITICAL")
            self._add_error("Unknown", 3603)
            return None

        for issue_tuple in result_list:
            result_dict = {
                'id': issue_tuple[0],
                'key': issue_tuple[1],
                'type': issue_tuple[2],
                'channel':issue_tuple[3],
                'testerID': issue_tuple[4],
                'projectID': issue_tuple[5],
                'time': issue_tuple[6],
                'softwareVersion': issue_tuple[7]
            }
            return_list.append(result_dict)
        
        self.l.log(f"{len(return_list)} issues found in the database for project key:{project_key}\id:{project_id}", "RUN")
        return return_list


#FIXME remove test after dev


if __name__ == "__main__":
    from Logger import Logger
    root_dir = os.path.dirname(__file__)
    logger = Logger(root_dir, "DEBUG")
    handler = DBHandler(logger, root_dir)
    res = handler._check_issue_existence("Test-2")
    print(res)
    print(handler.errors)
    print(len(handler.errors))
    print(handler.get_single_issue_info("Test-2"))
    print(handler.get_all_project_issues_info("Test"))
    print(handler.get_all_project_issues_info(project_id=36))
    print(handler.errors)
    print(handler.get_all_project_issues_info(37))

    print(handler.errors)
