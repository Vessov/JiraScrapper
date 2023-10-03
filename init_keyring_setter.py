import keyring
import yaml
import os
import random, string
import time
from sys import argv
from alive_progress import alive_bar

root_dir = os.path.dirname(__file__)
init_config_file = os.path.join(root_dir, "settings", "init_config copy.yaml")
JIRA_NAMESPACE = 'JIRA'
MAIL_NAMESPACE = "MAIL"
DB_NAMESPACE = "DB"


def set_jira_vars(api_key, server, mail):

    keyring.set_password(JIRA_NAMESPACE, "JIRA-API-KEY", api_key)
    keyring.set_password(JIRA_NAMESPACE, "JIRA-SERVER", server)
    keyring.set_password(JIRA_NAMESPACE, "JIRA-MAIL", mail)

    check_api = keyring.get_password(JIRA_NAMESPACE, "JIRA-API-KEY")
    check_server = keyring.get_password(JIRA_NAMESPACE, "JIRA-SERVER")
    check_mail = keyring.get_password(JIRA_NAMESPACE, "JIRA-MAIL")

    try:
        assert check_api == api_key
        assert check_server == server
        assert check_mail == mail
        return True
    except AssertionError as aerr:
        print(aerr)
        return False

def set_mail_vars(username, password, sender, receiver):
    
    keyring.set_password(MAIL_NAMESPACE, "MAIL-USER", username)
    keyring.set_password(MAIL_NAMESPACE, "MAIL-PASS", password)
    keyring.set_password(MAIL_NAMESPACE, "MAIL-SENDER", sender)
    keyring.set_password(MAIL_NAMESPACE, "MAIL-RECEIVER", receiver)

    check_user = keyring.get_password(MAIL_NAMESPACE, "MAIL-USER")
    check_pass = keyring.get_password(MAIL_NAMESPACE, "MAIL-PASS")
    check_sender = keyring.get_password(MAIL_NAMESPACE, "MAIL-SENDER")
    check_receiver = keyring.get_password(MAIL_NAMESPACE, "MAIL-RECEIVER")

    try:
        assert check_user == username
        assert check_pass == password
        assert check_sender == sender
        assert check_receiver == receiver
        return True
    except AssertionError as aerr:
        print(aerr)
        return False

def set_database_vars(user, password, database):
    
    keyring.set_password(DB_NAMESPACE, "DB-USER", user)
    keyring.set_password(DB_NAMESPACE, "DB-PASSWORD", password)
    keyring.set_password(DB_NAMESPACE, "DB-DATABASE", database)

    check_user = keyring.get_password(DB_NAMESPACE, "DB-USER")
    check_password = keyring.get_password(DB_NAMESPACE, "DB-PASSWORD")
    check_database = keyring.get_password(DB_NAMESPACE, "DB-DATABASE")

    try:
        assert check_user == user
        assert check_password == password
        assert check_database == database
        return True
    except AssertionError as aerr:
        print(aerr)
        return False

def obfuscate_init_config(filepath, rewrite_count:int=50):
    # anti-recovery function
    # overwrite init config file multiple times before deletion
    # to prevent any possibility of retrieving passwords/keys stored for first configuration

    def get_rand_string(num):
        res = ''.join(random.choices(string.ascii_uppercase + 
                                     string.digits +
                                     string.ascii_lowercase +
                                     string.punctuation, k=num))
        return res
    
    with alive_bar(rewrite_count) as bar:
        for _ in range(rewrite_count):
            with open(filepath, 'w') as file:
                credentials = {}

                jira_api = get_rand_string(192)
                jira_server = get_rand_string(30)
                jira_mail = get_rand_string(24)

                credentials['jira'] = {
                    "APIKey": jira_api,
                    "server": jira_server,
                    "mail": jira_mail
                }

                mail_user = get_rand_string(12)
                mail_pass = get_rand_string(8)
                mail_sender = get_rand_string(24)
                mail_receiver = get_rand_string(24)

                credentials['mail'] = {
                    "username": mail_user,
                    "password": mail_pass,
                    "sender": mail_sender,
                    "receiver": mail_receiver
                }

                db_user = get_rand_string(9)
                db_pass = get_rand_string(10)
                db_database = get_rand_string(12)

                credentials['database'] = {
                    'user': db_user,
                    'password': db_pass,
                    'database': db_database
                }

                yaml.dump(credentials, file)
                time.sleep(0.01)
                bar()

def keyring_setter(selfkill:bool=False):

    # load initial configuration file
    with open(init_config_file, 'r') as file:
        init_config = yaml.load(file, yaml.SafeLoader)

        credentials:dict = init_config['credentials']
        jira_cred:dict = credentials['jira']
        mail_cred:dict = credentials['mail']
        db_cred:dict = credentials['database']

        jira_api_key = jira_cred['APIKey']
        jira_server = jira_cred['server']
        jira_mail = jira_cred['mail']

        mail_username = mail_cred["username"]
        mail_password = mail_cred["password"]
        mail_sender = mail_cred["sender"]
        mail_receiver = mail_cred['receiver']

        database_user = db_cred['user']
        database_password = db_cred['password']
        database_database = db_cred['database']

    jira_stat = set_jira_vars(jira_api_key, jira_server, jira_mail)
    mail_stat = set_mail_vars(mail_username, mail_password, mail_sender, mail_receiver)
    db_stat = set_database_vars(database_user, database_password, database_database)

    if jira_stat and mail_stat and db_stat:
        print("Correctly created keyring variables")
        print("Obfuscating initial config file before deletion")
        obfuscate_init_config(init_config_file)
        print("Init config file obfuscated, deleting")
        os.remove(init_config_file)
        print("Init config file deleted")

        if (len(argv) > 1 and argv[1] == "\kill") or selfkill:
            print("Self-destructing the script")
            time.sleep(1)
            print("It's getting dark")
            time.sleep(0.5)
            print("Goodnight")
            # os.remove(__file__)

if __name__ == "__main__":
    keyring_setter()

    def _checker():
        check_user = keyring.get_password(MAIL_NAMESPACE, "MAIL-USER")
        check_pass = keyring.get_password(MAIL_NAMESPACE, "MAIL-PASS")
        check_sender = keyring.get_password(MAIL_NAMESPACE, "MAIL-SENDER")
        check_receiver = keyring.get_password(MAIL_NAMESPACE, "MAIL-RECEIVER")
        check_api = keyring.get_password(JIRA_NAMESPACE, "JIRA-API-KEY")
        check_server = keyring.get_password(JIRA_NAMESPACE, "JIRA-SERVER")
        check_mail = keyring.get_password(JIRA_NAMESPACE, "JIRA-MAIL")
        check_db_user = keyring.get_password(DB_NAMESPACE, "DB-USER")
        check_db_pass = keyring.get_password(DB_NAMESPACE, "DB-PASSWORD")
        check_db_database = keyring.get_password(DB_NAMESPACE, "DB-DATABASE")

        print("Mail user:   ", check_user)
        print("Mail pass:   ", check_pass)
        print("Mail sender:   ", check_sender)
        print("Mail receiver:   ", check_receiver)
        print("Jira api:   ", check_api)
        print("Jira server:   ", check_server)
        print("Jira mail:   ", check_mail)
        print("DB user:     ", check_db_user)
        print("DB pass:     ", check_db_pass)
        print("DB database:     ", check_db_database)

    _checker()
