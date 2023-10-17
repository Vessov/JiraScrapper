import mysql.connector
import os
import yaml


class TableInitializer:

    # define how the necessary tables are created
    standard_tables = {
    "Testers": "CREATE TABLE Testers (TesterID INT AUTO_INCREMENT PRIMARY KEY, Username VARCHAR(255), Name VARCHAR(255), Surname VARCHAR(255), Company VARCHAR(255))",
    "Projects": "CREATE TABLE Projects (ProjectID INT AUTO_INCREMENT PRIMARY KEY, ProjectKey VARCHAR(255), ProviderID VARCHAR(255), DeviceType VARCHAR(255), ProductID VARCHAR(255), ProjectName VARCHAR(255))",
    "Issues": "CREATE TABLE Issues (TestID INT AUTO_INCREMENT PRIMARY KEY, TestKey VARCHAR(255), TestType VARCHAR(255), DistChannel VARCHAR(255), TesterID INT, ProjectID INT, FOREIGN KEY (TesterID) REFERENCES testers(TesterID) , FOREIGN KEY (ProjectID) REFERENCES projects(ProjectID), Time FLOAT(4))"
    }

    def __init__(self, root_dir, logger) -> None:
        
        self.root_dir = root_dir
        self.logger = logger
        self.config_file = os.path.join(root_dir, "settings", "config.yaml")
        self.db_namespace = "DB"

        system = os.name
        if system == "nt":
            import keyring as kr
        elif system == "posix":
            import keyring as kr
            from keyrings.cryptfile.cryptfile import CryptFileKeyring
            krcrypt = CryptFileKeyring()
            krcrypt.keyring_key = os.getenv('KRCRYPT_PASS')
            kr.set_keyring(krcrypt)
        
        self.logger.log("Connecting to database", "DEBUG")

        # get configuration data from config file
        with open(self.config_file, 'r') as file:
            config = yaml.load(file, yaml.SafeLoader)
            credentials:dict = config['credentials']
            db_creds:dict = credentials['database']
            host_entry = db_creds['host']
            user_entry = db_creds['user']
            password_entry = db_creds['password']
            database_entry = db_creds['database']

            self.logger.log("Config file read", "DEBUG")
            self.logger.log(f"Host ENV VAR key: {host_entry}", "DEBUG")
            self.logger.log(f"User ENV VAR key: {user_entry}", "DEBUG")
            self.logger.log(f"Password ENV VAR key: {password_entry}", "DEBUG")
            self.logger.log(f"Database ENV VAR key: {database_entry}", "DEBUG")

            # get obscured login data, stored in env. variables    
            self.host_data = host_entry  # host data stored plain in config file
            self.user_data = kr.get_password(self.db_namespace, user_entry)
            self.password_data = kr.get_password(self.db_namespace, password_entry)
            self.database_data = kr.get_password(self.db_namespace, database_entry)

            self.logger.log("Obscured data retrieved", "DEBUG")

            # get the list of necessary tables
            self.tables:list = config['tables']

            self.logger.log(f"Required tables: {self.tables}", "DEBUG")

    def _connect(self):

        # achieve database connection
        try:
            db = mysql.connector.connect(
                host=self.host_data,
                user=self.user_data,
                password=self.password_data,
                database=self.database_data
            )
            return db
        
        except mysql.connector.errors.ProgrammingError as perr:
            self.logger.log("Connection not achieved", "ERROR")
            self.logger.log(f"Error message: '{perr}'", "ERROR")
            return False

    def update_tables(self):

        database = self._connect()

        if database is False:
            return False

        connected = database.is_connected()

        if connected:
            self.logger.log("Connection achieved", "DEBUG")
            server_info = database.get_server_info()
            self.logger.log(f"Server info: {server_info}", "DEBUG")

            cursor = database.cursor()
            to_execute = []
            found_tables = []

            # get the list of already existing tables
            cursor.execute("SHOW TABLES")
            for data in cursor:
                found_tables.append(data[0])
            
            self.logger.log(f"Currently existing tables: {found_tables}", "DEBUG")

            # check if all necessary tables are present in the database
            for table in self.tables:
                if table.lower() not in found_tables:
                    self.logger.log(f"Table {table} not found in existing tables", "DEBUG")
                    add_table = self.standard_tables[table]
                    to_execute.append(add_table)

            # if any tables are missing - create them
            if not len(to_execute) == 0:
                for query in to_execute:
                    cursor.execute(query)

                self.logger.log("Tables created, disconnecting from database", "DEBUG")
            else:
                self.logger.log("All tables present, disconnecting from database", "DEBUG")
            # terminate database connection
            database.disconnect()
            return True

        else:
            self.logger.log("Connection broken/not established, unable to proceed", "ERROR")


if __name__ == "__main__":
    from Logger import Logger
    root_dir = os.path.dirname(__file__)
    logger = Logger(root_dir, "DEBUG")

    tbinit = TableInitializer(root_dir, logger)
    tbinit.update_tables()
    