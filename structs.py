from jira import JIRA, Issue, JIRAError
from Logger import Logger


class TestTypeIssue:

    def __init__(self,
                 logger,
                 key:str,
                 test_type:str, 
                 channel:str, 
                 tester:str, 
                 time:int,
                 version:str) -> None:
        
        self.l = logger
        self.key = key
        self.test_type = test_type
        self.channel = channel
        self.tester = tester
        self.time = time
        self.version = version
        self.l.log(f"Initialized Issue {self.key}", "DEBUG")

    def get_specs(self) -> dict:
        self.l.log(f"Returning all data for Issue {self.key}", "DEBUG")
        return vars(self)


class Project:
    project_issues = []
    parents = {}

    def __init__(self,
                 logger:Logger,
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

        def check_main_errors_dict():
            check_main = self.errors.get('main')
            if check_main is None:
                self.errors['main'] = []

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
            check_main_errors_dict()
            self.errors["main"].append(2101)
            self.l.log(f"No matching developer found for project {self.key}!", "ERROR")
            self.developer = "Unknown"
        
        # check if project is present in config file
        if self.key not in projects_dict.keys():
            check_main_errors_dict()
            self.errors["main"].append(2102)
            self.l.log(f"Project with the key {self.key} is not present in the configuration file", "ERROR")
            

        # get full name of the project
        for proj_key, proj_name in projects_dict.items():
            if self.key == proj_key:
                self.name = proj_name['name']

        # log results
        if self.name is not None:
            self.l.log(f"Name {self.name} associated with project {self.key}", "DEBUG")
        else:
            check_main_errors_dict()
            self.errors["main"].append(2103)
            self.l.log(f"No matching name found for project {self.key}!", "ERROR")
    
    def _add_error(self, epicKey:str, issueKey:str, errorCode:int):

        if self.errors.get(epicKey) is None:
            self.errors[epicKey] = {}
        if issueKey not in self.errors[epicKey].keys():
            self.errors[epicKey][issueKey] = []
        if errorCode not in self.errors[epicKey][issueKey]:
            self.errors[epicKey][issueKey].append(errorCode)

    def _get_parent(self, issueKey) -> Issue:
        try:

            self.l.log(f"Starting search for parent of issue {issueKey}", "DEBUG")
            issue = self.j.issue(issueKey)
            issueParent = issue.get_field("parent")
            parentKey = issueParent.key
            epic = self.j.issue(parentKey)
            self.l.log(f"Parent key found: {epic.key}", "DEBUG")

            if epic.key not in self.parents:
                # create empty dict to store parent info - distribution channel and software version
                self.parents[epic.key] = {}

            return epic
        
        except JIRAError as jerr:

            self._add_error("Unknown", issueKey, 2301)
            self.l.log(f"Error when getting parent of issue {issueKey} in project {self.key}: {jerr}", "ERROR")
            
            return None

    def _get_channel(self, issueKey, parent:Issue) -> str:

        epic = parent

        if epic is None:

            self.l.log(f"Can't find proper distribution channel due to lack of parent of issue {issueKey}", "ERROR")
            self._add_error("Unknown", issueKey, 2401)

            return None
        
        self.l.log(f"Checking if {parent.key} is present in self.parents", "DEBUG")

        if epic.key in self.parents:

            epicdict:dict = self.parents[epic.key]
            chan_type = epicdict.get("channelType")

            if chan_type is not None:

                self.l.log(f"Epic {epic.key} found, channel is {chan_type}", "DEBUG")
                channeltype = chan_type

                return channeltype
        
        else:

            self.l.log(f"Epic {epic.key} not in parents, or does not have associated channel type", "DEBUG")

        superEpicKey = None
        channeltype = None
        inwardIssue_found = False
        
        self.l.log(f"Iterating over linked issues of epic {epic.key}", "DEBUG")

        for i in range(len(epic.fields.issuelinks)):

            linkedIssueDict:dict = epic.raw['fields']['issuelinks'][i]
            
            if 'inwardIssue' in linkedIssueDict.keys():

                inwardIssue_found = True
                self.l.log(f"Found inward linked issue", "DEBUG")
                linkedIssueType = linkedIssueDict['inwardIssue']['fields']['issuetype']['name']

                if linkedIssueType == "SuperEpic":

                    self.l.log(f"Inward linked issue is confirmed as SuperEpic", "DEBUG")
                    superEpicKey = linkedIssueDict['inwardIssue']['key']
                    superEpic = self.j.issue(superEpicKey)
                    channeltype = superEpic.fields.summary
                    self.parents[epic.key]["channelType"] = channeltype

                    return channeltype
            
        if inwardIssue_found == False:
            self.l.log(f"Epic {parent.key} has no valid SuperEpic links", "ERROR")
            self._add_error(parent.key, issueKey, 2402)
            
        if superEpicKey is None or channeltype is None:

            self.l.log(f"Can't find proper distribution channel for issue {issueKey} and epic {epic.key}", "ERROR")
            self._add_error(parent.key, issueKey, 2403)
            
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
            issueParent = issue.get_field("parent")
            parentKey = issueParent.key
            self._add_error(parentKey, issueKey, 2501)
            self.l.log(f"No name found for tester in issue {issueKey}", "ERROR")
            
            return None

    def gather_issues(self, limit:int=500):
        self.l.log(f"Starting gathering of max {limit} issues for project {self.key}", "DEBUG")
        issues = []

        jql_search = f'''project="{self.key}" AND issuetype = "Test Type"'''

        # appending to list and then interating over the issues contained in that list is 30% faster
        # than commencing any operations in the search_issues for loop
        for singleIssue in self.j.search_issues(jql_str=jql_search, maxResults=limit):
            issues.append(singleIssue)
        
        for singleIssue in issues:
            issueKey = singleIssue.key
            issueName = singleIssue.fields.summary
            aggregateTime = singleIssue.raw['fields']['aggregatetimespent']

            if aggregateTime is None:
                aggregateTime = 0

            issueTime = round((int(aggregateTime) / 3600), 1)  # divide the aggregated time (which is in seconds) by 3600 to get hours and round to 1 decimal digit
            parentIssue = self._get_parent(issueKey)

            # check if parent issue in self.parents
            if parentIssue is not None and parentIssue.key in self.parents:

                epicdict:dict = self.parents[parentIssue.key]
                softver = epicdict.get("softVersion")
                if softver is not None:
                    softVersion = softver

                else:
                    parent_summary = parentIssue.fields.summary
                    softVersion = parent_summary.split(" ")[0]
                    self.parents[parentIssue.key]["softVersion"] = softVersion
                
                distributionChannel = self._get_channel(issueKey, parentIssue)
                if distributionChannel is None:
                    distributionChannel = "Unknown"
                

            elif parentIssue is not None:
                parent_summary = parentIssue.fields.summary
                softVersion = parent_summary.split(" ")[0]
                self.parents[parentIssue.key]["softVersion"] = softVersion

                distributionChannel = self._get_channel(issueKey, parentIssue)
                if distributionChannel is None:
                    distributionChannel = "Unknown"

            else:
                softVersion = "Unknown"
                distributionChannel = "Unknown"
            
            issueApprover = self._get_tester(issueKey)
            if issueApprover is None:
                issueApprover = "Unknown"

            self.l.log(f"Creating new issue {issueKey}, type: {issueName}, channel: {distributionChannel}, tester: {issueApprover}", "DEBUG")
            newIssue = TestTypeIssue(logger=self.l,
                             key=issueKey,
                             test_type=issueName,
                             channel=distributionChannel,
                             tester=issueApprover,
                             time=issueTime,
                             version=softVersion)
            
            self.l.log(f"Appending issue {issueKey} to project's {self.key} issues list", "DEBUG")
            self.project_issues.append(newIssue)
        
        self.l.log(f"Project {self.key} contains {len(self.project_issues)} issues", "RUN")
        
        return self.project_issues

