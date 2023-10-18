
# JiraScrapper

Data scrapper, deisgned to gather issues from Jira (set up to gather bug report info during mobile OS testing), format data and insert it into MySQL database. Created to get info about Test Matrices, time spent on testing, tester info, software version, and all other relevant information.


## Usage/Examples

**WARNING: For the corret working of JiraScrapper, the Jira architecture has to be set up in a particular way; this however is out of the scope of this project.**

To use the JiraScrapper, proceed as follows:

Clone project to the desired machine/server.  

Then, virtual environment should be set up inside the project directory.

Install all the necessary libraries from `requirements.txt` inside the venv. This can be achieved by running appropriate `pip` command in the venv in which the script will be running:  
`pip install -r requirements.txt`

The example files `config.yaml` and `init_config.yaml` should be filled with correct data - host data, API keys, logins, mails, passwords, etc.  

`config.yaml` should be filled only with non-vital information - testers data, mail host, database IP (or localhost), etc. The rest should be left as-is, as it will be used as entry info for keyring, in which the passwords and vital data will be securely stored after setup  

`init_config.yaml` should be filled with all the vital data, which should be stored as encrypted - passwords, logins, credentials, API keys, etc. This should be done as the last step before running the `Setup.py` script. After the data from `init_config.yaml` is read, correctly inputted into keyring, and confirmed to be set, the file will be overwritten multiple times and then deleted *(to assure that vital data can't be retrieved even by file restoration)*

After all config files were correctly set up, run `Setup.py`. This will store all the vital information in keyring and env variables, check the connection to the database, and create all the required architecture inside the database - database itself, all tables, input data for projects, testers, etc. All info will be stored in logs, so they should be checked if everything was correctly set up.

From this point on, the main `JiraScrapper.py` can be used to get all the data, process it and push it into database. For ease of use, it is recommended to run the whole package on a server, as to make the scrapper independent of the state of any personal machine.

How often the script will run should be tailored to the needs of specific case, however, to avoid handling too much data at once, it is recommended to schedule the script to run every between 1 to 8 hours. This can be achieved either by using **Windows Task Scheduler** on Windows, or **cron** on Unix systems. Example:

```
0 */2 * * * /home/user/JiraScrapper/env/bin/python /home/user/JiraScrapper/JiraScrapper.py 
```
This will run the JiraScrapper in the virtual environment every two hours.

## Database Architecture

Database consist of three main tables:
- Testers
- Projects
- Issues

**Testers** table consists of columns as follows:
| Column | Description                |
| :-------- | :------------------------- |
| TesterID | Auto-Incremented primary key | 
| Username | Unique username of the tester |
| Name | First name of the tester |
| Surname | Last name of the tester |
| Company | For which company the tester works |  

\
**Projects** table consists of columns as follows:  
| Column | Description |
| :------| :-----------|
| ProjectID | Auto-Incremented primary key |
| ProjectKey | Key used in Jira for project |
| ProviderID | ID of provider associated with the project |
| DeviceType | Type of device that is developed in the project |
| ProductID | Internal projects' catalogue ID used in sales, etc. |
| ProjectName | Full name of the project, ex. device market name |

\
**Issues** table consists of columns as follows:
| Column | Description |
| :------| :-----------|
| TestID | Auto-Incremented primary key |
| TestKey | Key associated with issue in Jira |
| TestType | Type of test matrix associated with issue |
| DistChannel | With which distribution channel issue is associated |
| TesterID | Foreign key linking to **Testers** table (many-to-one) |
| ProjectID | Foreign key linking to **Projects** table (many-to-one) |
| Time | Logged time worked on this issue |
| SoftwareVersion | Software version with which the issue is associated |

\
Additionally, to ensure easy linking with visualisation/data analisys tools (ex. PowerBI), a view is created in the Database.
**AnalysisView**
| Column | Description |
| :------| :-----------|
| SoftwareVersion | From **Issues** table |
| TestKey | From **Issues** table |
| TestType | From **Issues** table |
| DistChannel | From **Issues** table |
| Time | From **Issues** table |
| ProductID | From **Projects** table |
| Username | From **Testers** table |


## Notifications

Whenever JiraScrapper encounteres any problems, it will log them, and inform the user at the end of the process.

First, the script will attempt to solve the problems - by trying to reestablish connections, recreate the database, tables or records, etc. However, if any problem will be encountered during the repair process, all the info will be gathered in logs, and then all logs will be sent, alongside appropriate message, by e-mail to the account designated as *receiver* in config file.

## Tech Stack

**Database:** MySQL

**Language:** Python 3.11.5

**Libraries:** yaml, smtplib, keyring, keyrings.cryptfile, jira


## Authors

- [Tomasz "Vesper" Winecki](https://github.com/Vessov)


## License

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
