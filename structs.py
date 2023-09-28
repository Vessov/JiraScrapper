from jira import JIRA
import yaml

# TODO implement some kind of email notifier

class Issue:

    def __init__(self,
                 logger,
                 key:str,
                 test_type:str, 
                 channel:str, 
                 tester:str, 
                 time:int) -> None:
        
        self.l = logger
        self.key = key
        self.test_type = test_type
        self.channel = channel
        self.tester = tester
        self.time = time
        self.l.log(f"Initialized Issue {self.key}", "DEBUG")

    def get_specs(self) -> dict:
        self.l.log(f"Returning all data for Issue {self.key}", "DEBUG")
        return vars(self)


class Project:
    project_issues = []

    def __init__(self,
                 logger,
                 jira:JIRA,
                 key:str,
                 developers_dict:dict,
                 projects_dict:dict) -> None:
        self.l = logger
        self.key = key
        self.j = jira
        self.developer = None
        self.name = None
        self.l.log(f"Initialization of project {self.key}", "RUN")
        self.errors = {}

        # create nameMap to easily access custom fields returned form Jira
        allfields = self.j.fields()
        self.nameMap = {field['name']:field['id'] for field in allfields}

        # get developer associated with project
        for developer, proj_list in developers_dict.items():
            if key in proj_list:
                self.developer = developer
        #log results
        if self.developer is not None:
            self.l.log(f"Developer {self.developer} assigned to project {self.key}", "DEBUG")
        else:
            self.errors["dev"] = f"No developer found for project {self.key}"
            self.l.log(f"No matching developer found for project {self.key}!", "ERROR")
        
        # get full name of the project
        for proj_key, proj_name in projects_dict.items():
            if self.key == proj_key:
                self.name = proj_name
        # log results
        if self.name is not None:
            self.l.log(f"Name {self.name} associated with project {self.key}", "DEBUG")
        else:
            self.errors["name"] = f"Couldn't match any name with project {self.key}"
            self.l.log(f"No matching name found for project {self.key}!", "ERROR")
    
    def _get_channel(self, issueKey) -> str:
        self.l.log(f"Starting search for parent of issue {issueKey}", "DEBUG")
        issue = self.j.issue(issueKey)
        issueParent = issue.get_field("parent")
        epic = self.j.issue(issueParent)
        superEpicKey = None
        channeltype = None
        
        self.l.log(f"Iterating over linked issues of epic {epic.key}", "DEBUG")

        for i in range(len(epic.fields.issuelinks)):
            linkedIssueDict:dict = epic.raw['fields']['issuelinks'][i]
            
            if 'inwardIssue' in linkedIssueDict.keys():
                self.l.log(f"Found inward linked issue", "DEBUG")
                linkedIssueType = linkedIssueDict['inwardIssue']['fields']['issuetype']['name']

                if linkedIssueType == "SuperEpic":
                    self.l.log(f"Inward linked issue is confirmed as SuperEpic", "DEBUG")
                    superEpicKey = linkedIssueDict['inwardIssue']['key']
                    superEpic = self.j.issue(superEpicKey)
                    channeltype = superEpic.fields.summary
                    return channeltype
            
        if superEpicKey is None or channeltype is None:
            self.l.log(f"Can't find proper distribution channel for issue {issueKey} and epic {epic.key}", "ERROR")
            self.errors['dist_channel'] = f"Can't find distribution channel/SuperEpic fo issue: {issueKey}, epic: {epic.key}"
            return None

    def _get_tester(self, issueKey) -> str:
        self.l.log(f"Starting search for tester assigned to issue {issueKey}", "DEBUG")
        issue = self.j.issue(issueKey)
        try:
            userlist = getattr(issue.fields, self.nameMap["Approvers"])
            user = userlist[0]
            tester = user.displayName
            self.l.log(f"Tester {tester} found assigned to issue {issueKey}", "DEBUG")
            return tester
        except:
            self.errors["tester"] = f"Tester name not found in Approvers for issue {issueKey}"
            self.l.log(f"No name found for tester in issue {issueKey}", "ERROR")
            return None

    def gather_issues(self, limit:int=500):
        self.l.log(f"Starting gathering of max {limit} issues for project {self.key}", "DEBUG")

        jql_search = f'''project="{self.key}" AND issuetype = "Test Type"'''

        for singleIssue in self.j.search_issues(jql_str=jql_search, maxResults=limit):
            issueKey = singleIssue.key
            issueName = singleIssue.fields.summary
            issueTime = round((int(singleIssue.raw['fields']['aggregatetimespent']) / 3600), 1)  # divide the aggregated time (which is in seconds) by 3600 to get hours and round to 1 decimal digit
            distributionChannel = self._get_channel(issueKey)
            issueApprover = self._get_tester(issueKey)

            self.l.log(f"Creating new issue {issueKey}, type: {issueName}, channel: {distributionChannel}, tester: {issueApprover}", "DEBUG")
            newIssue = Issue(logger=self.l,
                             key=issueKey,
                             test_type=issueName,
                             channel=distributionChannel,
                             tester=issueApprover,
                             time=issueTime)
            
            self.l.log(f"Appending issue {issueKey} to project's {self.key} issues list", "DEBUG")
            self.project_issues.append(newIssue)
        
        self.l.log(f"Project {self.key} contains {len(self.project_issues)} issues", "RUN")
        
        return self.project_issues
    

