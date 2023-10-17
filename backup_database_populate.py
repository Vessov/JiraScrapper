import os
import yaml
import mysql.connector


class DBPopulator:

    def __init__(self, root_dir, logger) -> None:
        
        self.root_dir = root_dir
        self.config_file = os.path.join(self.root_dir, "settings", "config.yaml")
        self.db_namespace = "DB"
        self.logger = logger

        system = os.name
        if system == "nt":
            import keyring as kr
        elif system == "posix":
            import keyring as kr
            from keyrings.cryptfile.cryptfile import CryptFileKeyring
            krcrypt = CryptFileKeyring()
            krcrypt.keyring_key = os.getenv('KRCRYPT_PASS')
            kr.set_keyring(krcrypt)
        
        self.logger.log("Starting the database check", "DEBUG")

        with open(self.config_file, 'r', encoding='utf-8') as file:
            config = yaml.load(file, yaml.SafeLoader)
            self.credentials:dict = config['credentials']
            self.db_creds:dict = self.credentials['database']
            self.host_entry = self.db_creds['host']
            self.user_entry = self.db_creds['user']
            self.password_entry = self.db_creds['password']
            self.database_entry = self.db_creds['database']

            self.logger.log("Config file read", "DEBUG")
            self.logger.log(f"Host ENV VAR key: {self.host_entry}", "DEBUG")
            self.logger.log(f"User ENV VAR key: {self.user_entry}", "DEBUG")
            self.logger.log(f"Password ENV VAR key: {self.password_entry}", "DEBUG")
            self.logger.log(f"Database ENV VAR key: {self.database_entry}", "DEBUG")

            # get obscured login data, stored in env. variables    
            self.host_data = self.host_entry  # host data stored plain in config file
            self.user_data = kr.get_password(self.db_namespace, self.user_entry)
            self.password_data = kr.get_password(self.db_namespace, self.password_entry)
            self.database_data = kr.get_password(self.db_namespace, self.database_entry)

            self.logger.log("Obscured data retrieved", "DEBUG")

            # get the list of necessary tables, projects, testers
            self.tables:list = config['tables']
            self.projects:dict = config['data']['projects']
            self.developers:dict = config['data']['developers']
            self.testers:dict = config['testers']

            self.logger.log(f"Required tables: {self.tables}", "DEBUG")

    def _establish_connection(self, recursion_depth:int = 5) -> mysql.connector.MySQLConnection | bool:
        recursion_depth -= 1
        self.logger.log("Connecting to database", "DEBUG")
        try:
            db = mysql.connector.connect(
                host=self.host_data,
                user=self.user_data,
                password=self.password_data,
                database=self.database_data,
                use_unicode=True,
                charset="utf8"
            )

            return db

        except mysql.connector.errors.ProgrammingError as perr:
            if recursion_depth <= 0:
                self.logger.log("Maximum recursion level reached, connection not established", "ERROR")
                return False
            
            self.logger.log("Connection not achieved", "ERROR")
            self.logger.log(f"Error message: '{perr}'", "ERROR")
            self.logger.log("Checking if db exists and trying to recreate if not", "DEBUG")
            result = self._create_db()

            if result is True:
                self.logger.log("Database should exist", "DEBUG")
                self.logger.log("Trying to reconnect", "DEBUG")
                recon_result = self._establish_connection(recursion_depth)
                self.logger.log(f"Connection status: {'Achieved' if recon_result is not False else 'Not achieved'}")
                return recon_result
            else:
                self.logger.log("Couldn't correctly create database", "DEBUG")
                return False

    def _populate_testers(self,
        cursor:mysql.connector.MySQLConnection.cursor, 
        connection:mysql.connector.MySQLConnection) -> bool:

        query = "INSERT INTO testers (Username, Name, Surname, Company) VALUES (%s, %s, %s, %s)"

        def get_current_testers():
            #get currently existing testers
            self.logger.log("Collecting current testers", "DEBUG")
            found_testers = []
            cursor.execute("SELECT * FROM testers")
            for tester_tuple in cursor:
                found_testers.append(tester_tuple[1])
            self.logger.log(f"Found testers: {found_testers}", "DEBUG")
            return found_testers

        found_testers = get_current_testers()
        for tester in self.testers.keys():
            if tester not in found_testers:

                self.logger.log(f"Tester {tester} not found in database. Adding", "DEBUG")

                username = tester
                name = self.testers[tester]['name']
                surname = self.testers[tester]['surname']
                company = self.testers[tester]['company']
                placeholder = (username, name, surname, company)
                cursor.execute(query, placeholder)
                self.logger.log(f"Tester {tester} added", "DEBUG")
        
        connection.commit()
        
        try:
            self.logger.log("Checking if commited", "DEBUG")
            found_testers = get_current_testers()
            for tester in self.testers.keys():
                assert tester in found_testers
            self.logger.log("All testers present in database", "DEBUG")
            return True

        except AssertionError as aerr:
            base = set(self.testers)
            diff = [x for x in found_testers if x not in base]
            self.logger.log(f"Error encountered: {aerr}", "ERROR")
            self.logger.log(f"Testers still not added: {diff}", "ERROR")
            return False

    def _populate_projects(self,
            cursor:mysql.connector.MySQLConnection.cursor,
            connection:mysql.connector.MySQLConnection) -> bool:
        
        query = "INSERT INTO projects (ProjectKey, ProviderID, DeviceType, ProductID, ProjectName) VALUES (%s, %s, %s, %s, %s)"

        def get_current_projects():
            self.logger.log("Collecting current projects", "DEBUG")
            found_projects = []
            cursor.execute("SELECT * FROM projects")
            for project_tuple in cursor:
                found_projects.append(project_tuple[1])
            self.logger.log(f"Found projects: {found_projects}", "DEBUG")
            return found_projects
        
        def find_provider(project):
            for provider, projects_list in self.developers.items():
                if project in projects_list:
                    return provider

        found_projects = get_current_projects()
        for project in self.projects.keys():
            if project not in found_projects:
                self.logger.log(f"Project {project} not found in database. Adding", "DEBUG")

                provider = find_provider(project)
                device_type = self.projects[project]['type']
                product_id = self.projects[project]['ID']
                project_name = self.projects[project]['name']
                placeholder = (project, provider, device_type, product_id, project_name)

                cursor.execute(query, placeholder)
                self.logger.log(f"Project {project} added", "DEBUG")
        
        connection.commit()
        
        try:
            self.logger.log("Checking if commited", "DEBUG")
            found_projects = get_current_projects()
            for project in self.projects.keys():
                assert project in found_projects
            self.logger.log("All projects present in database", "DEBUG")
            return True
        
        except AssertionError as aerr:
            base = set(self.projects)
            diff = [x for x in found_projects if x not in base]
            self.logger.log(f"Error encountered: {aerr}", "ERROR")
            self.logger.log(f"Projects still not added: {diff}", "ERROR")
            return False

    def _create_db(self) -> bool:

        self.logger.log("Connecting to SQL without specified database", "DEBUG")

        try:
            db = mysql.connector.connect(
                host=self.host_data,
                user=self.user_data,
                password=self.password_data
            )
            if db.is_connected():
                self.logger.log("Connection established", "DEBUG")
            else:
                self.logger.log("Connection not achieved - unknown error!", "ERROR")
                return False
        
        except mysql.connector.errors.ProgrammingError as perr:
            self.logger.log("Connection not achieved", "ERROR")
            self.logger.log(f"Error message: '{perr}'", "ERROR")
            return False
        
        cursor = db.cursor()
        cursor.execute("SHOW DATABASES")
        found_dbs = []
        for db_result in cursor:
            found_dbs.append(db_result)
        
        if not self.database_data in found_dbs:
            self.logger.log(f"Database {self.database_data} not found, creating", "DEBUG")
            cursor.execute(f"CREATE DATABASE {self.database_data}")

            # after creating the db, try connecting to it
            db.disconnect()

            try:
                db = mysql.connector.connect(
                    host=self.host_data,
                    user=self.user_data,
                    password=self.password_data,
                    database=self.database_data
                )
            except mysql.connector.errors.ProgrammingError as perr:
                self.logger.log("Connection not achieved", "ERROR")
                self.logger.log(f"Error message: '{perr}'", "ERROR")
                return False

            if db.is_connected():
                self.logger.log("Database correctly created and connected to", "DEBUG")
                import init_database_tables as init_db
                self.logger.log("Creating required tables", "DEBUG")
                result = init_db.update_tables(db)
                if result is True:
                    self.logger.log("Database correctly created, tables updated", "DEBUG")
                    db.disconnect()
                    return True
                else:
                    self.logger.log("Couldn't properly update tables", "ERROR")
                    db.disconnect()
                    return False

    def populate_database(self) -> bool:
        self.logger.log("Initiate populating database", "DEBUG")

        db = self._establish_connection()

        if db is not False and db.is_connected():
            self.logger.log("Connection correctly achieved", "DEBUG")
        else:
            self.logger.log("Connection not achieved!", "ERROR")
            self.logger.log("Populating stopped", "DEBUG")
            return False
        
        cursor = db.cursor()

        testers_table_population = self._populate_testers(cursor, db)
        projects_table_population = self._populate_projects(cursor, db)

        if testers_table_population and projects_table_population:
            self.logger.log("Database correctly populated", "DEBUG")
            return True
        
        else:
            results = [testers_table_population, projects_table_population]
            # get a list of names of variables that returned false 
            problems = [[name for name in globals() if globals()[name] == y] for y in results if y is False]
            for problem in problems:
                self.logger.log(f"Problem encountered: {problem} not achieved correctly - returned False")
            
            return False


if __name__ == "__main__":
    from Logger import Logger
    root_dir = os.path.dirname(__file__)
    logger = Logger(root_dir, "DEBUG")
    populator = DBPopulator(root_dir, logger)
    populator.populate_database()