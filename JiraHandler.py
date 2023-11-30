import os
import yaml
import keyring as kr
from jira import JIRA, exceptions
from typing import Protocol


class Logger(Protocol):
    def log(self, message:str, level:str):
        pass


class JiraHandler:
    errors = {}

    def __init__(self, logger:Logger, rdir:str) -> None:
        self._root_dir = rdir
        self.l = logger
        self.jira_namespace = "JIRA"

        self.l.log("Initializing JIRA Connector class", "DEBUG")
        try:
            config_file = os.path.join(self._root_dir, "settings", "config.yaml")

            with open(config_file, 'r') as file:
                config = yaml.load(file, yaml.SafeLoader)
                credentials:dict = config["credentials"]
                jira_creds:dict = credentials["jira"]
                apiKey = jira_creds["APIKey"]
                server = jira_creds["server"]
                email = jira_creds["mail"]

            self.jira:JIRA = self._establish_connection(apiKey, server, email)

            if isinstance(self.jira, JIRA):
                allfields = self.jira.fields()
                self.nameMap = {field['name']:field['id'] for field in allfields}
            else:
                self.errors["jira"] = 4102
                self.l.log(f"Couldn't get correct JIRA object instance", "CRITICAL")
        
        except Exception as err:
            self.errors["main"] = 4101
            self.l.log(f"Couldn't complete instantiation", "CRITICAL")
            self.l.log(f"Error message: {err}", "WARNING")
            self.l.log(f"Config path: {config_file}", "WARNING")
            self.l.log(f"Connector type: {type(self.jira)}", "WARNING")

            

    def _establish_connection(self, apiKey, server, email) -> JIRA | None:
        
        retrieved_apiKey = kr.get_password(self.jira_namespace, apiKey)
        retrieved_server = kr.get_password(self.jira_namespace, server)
        retrieved_email = kr.get_password(self.jira_namespace, email)

        jiraOptions = {'server': retrieved_server}

        try:
            jira = JIRA(options=jiraOptions, basic_auth=(retrieved_email, retrieved_apiKey))
            session_id = jira.session()
            if session_id is not None:
                return jira
        
        except exceptions.JIRAError as jerr:
            self.l.log("Connection establishing error", "CRITICAL")
            status_code = jerr.status_code
            url = jerr.url
            text = jerr.text

            if status_code == 401:
                self.errors["connection"] = 4201
                self.l.log(f"Error message: {text}", "WARNING")
                self.l.log(f"URL: {url}", "WARNING")

            elif status_code == 404:
                self.errors["connection"] = 4202
                self.l.log(f"Error message: {text}", "WARNING")
                self.l.log(f"URL: {url}", "WARNING")

            else:
                self.errors["connection"] = 4203
                self.l.log(f"Status code: {status_code}")
                self.l.log(f"Error message: {text}", "WARNING")
                self.l.log(f"URL: {url}", "WARNING")
            
            return None

