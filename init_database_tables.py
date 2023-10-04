import mysql.connector
import os
import yaml
import keyring as kr
from Logger import Logger

root_dir = os.path.dirname(__file__)
config_file = os.path.join(root_dir, "settings", "config.yaml")
db_namespace = "DB"
logger = Logger(root_dir, "DEBUG")

# define how the necessary tables are created
standard_tables = {
    "Testers": "CREATE TABLE Testers (TesterID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(255), Name VARCHAR(255), Surname VARCHAR(255), Company VARCHAR(255))",
    "Projects": "CREATE TABLE Projects (ProjectID INT AUTO_INCREMENT PRIMARY KEY, ProjectKey VARCHAR(255), ProviderID VARCHAR(255), DeviceType VARCHAR(255), ProductID VARCHAR(255), ProjectName VARCHAR(255))",
    "Issues": "CREATE TABLE Issues (TestID INT AUTO_INCREMENT PRIMARY KEY, TestKey VARCHAR(255), TestType VARCHAR(255), DistChannel VARCHAR(255), TesterID INT, ProjectID INT, FOREIGN KEY (TesterID) REFERENCES testers(TesterID) , FOREIGN KEY (ProjectID) REFERENCES projects(ProjectID), Time FLOAT(4))"
}

# get configuration data from config file
with open(config_file, 'r') as file:
    config = yaml.load(file, yaml.SafeLoader)
    credentials:dict = config['credentials']
    db_creds:dict = credentials['database']
    host_entry = db_creds['host']
    user_entry = db_creds['user']
    password_entry = db_creds['password']
    database_entry = db_creds['database']

    logger.log("Config file read", "DEBUG")
    logger.log(f"Host ENV VAR key: {host_entry}", "DEBUG")
    logger.log(f"User ENV VAR key: {user_entry}", "DEBUG")
    logger.log(f"Password ENV VAR key: {password_entry}", "DEBUG")
    logger.log(f"Database ENV VAR key: {database_entry}", "DEBUG")

    # get obscured login data, stored in env. variables    
    host_data = host_entry  # host data stored plain in config file
    user_data = kr.get_password(db_namespace, user_entry)
    password_data = kr.get_password(db_namespace, password_entry)
    database_data = kr.get_password(db_namespace, database_entry)

    logger.log("Obscured data retrieved", "DEBUG")

    # get the list of necessary tables
    tables:list = config['tables']

    logger.log(f"Required tables: {tables}", "DEBUG")

logger.log("Connecting to database", "DEBUG")
# achieve database connection
try:
    db = mysql.connector.connect(
        host=host_data,
        user=user_data,
        password=password_data,
        database=database_data
    )
except mysql.connector.errors.ProgrammingError as perr:
    logger.log("Connection not achieved", "ERROR")
    logger.log(f"Error message: '{perr}'", "ERROR")

def update_tables():

    connected = db.is_connected()

    if connected:
        logger.log("Connection achieved", "DEBUG")
        server_info = db.get_server_info()
        logger.log(f"Server info: {server_info}", "DEBUG")

        cursor = db.cursor()
        to_execute = []
        found_tables = []

        # get the list of already existing tables
        cursor.execute("SHOW TABLES")
        for data in cursor:
            found_tables.append(data[0])
        
        logger.log(f"Currently existing tables: {found_tables}", "DEBUG")

        # check if all necessary tables are present in the database
        for table in tables:
            if table.lower() not in found_tables:
                logger.log(f"Table {table} not found in existing tables", "DEBUG")
                add_table = standard_tables[table]
                to_execute.append(add_table)

        # if any tables are missing - create them
        if not len(to_execute) == 0:
            for query in to_execute:
                cursor.execute(query)

            logger.log("Tables created, disconnecting from database", "DEBUG")
        else:
            logger.log("All tables present, disconnecting from database", "DEBUG")
        # terminate database connection
        db.disconnect()

    else:
        logger.log("Connection broken/not established, unable to proceed", "ERROR")

def main():
    update_tables()

if __name__ == "__main__":
    main()