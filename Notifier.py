import yaml, os
import smtplib, ssl, email
import keyring as kr
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta

class Notifier:

    def __init__(self, rdir) -> None:
        self._root_dir = rdir
        mail_namespace = 'MAIL'

        config_file = os.path.join(rdir, "settings", "config.yaml")

        with open(config_file, 'r') as file:
            config = yaml.load(file, yaml.SafeLoader)
            credentials:dict= config['credentials']
            mail_creds:dict = credentials['mail']
            host_entry = mail_creds['host']
            port_entry = mail_creds['port']
            username_entry = mail_creds['username']
            password_entry = mail_creds['password']
            sender_entry = mail_creds['sender']
            receiver_entry = mail_creds['receiver']
        
        self.host = host_entry
        self.port = port_entry
        self.username = kr.get_password(mail_namespace, username_entry)
        self.password = kr.get_password(mail_namespace, password_entry)
        self.sender = kr.get_password(mail_namespace, sender_entry)
        self.receiver = kr.get_password(mail_namespace, receiver_entry)

    def get_recent_logs(self, days:int=1):
        logs = []

        today = date.today()
        retention_border = today - timedelta(days=days)
        logs_dir = os.path.join(self._root_dir, "debug")

        for file in os.listdir(logs_dir):
            # only consider files with date and number in name
            if len(file) > 11:
                # strip everything except the date portion of name
                str_date = file.lstrip("logfile_").replace("_", "/")[0:-8]
                file_date = datetime.strptime(str_date, "%d/%m/%Y").date()
                if file_date >= retention_border:
                    full_path = os.path.join(logs_dir, file)
                    logs.append(full_path)
        
        return logs

    def notify_by_mail(self, errors:list, attach_logs:bool=True):
        errors_num = len(errors)

        subject = f"{errors_num} errors found!"

        msg = MIMEMultipart()

        msg["From"] = self.sender
        msg["To"] = self.receiver
        msg["Subject"] = subject

        body = ""

        for error in errors:
            if isinstance(error, dict):
                for err_type, message in error.items():
                    line = f"Error type: {err_type} \t\tError message: {message}\n\n"
                    body += line
            else:
                line = f"Error: {error}\n"
                body += line
        
        msg.attach(MIMEText(body, "plain"))

        if attach_logs:
            log_files = self.get_recent_logs()

            for log_file in log_files:
                filename = log_file[-26:]
                print(filename)

                with open(log_file, 'rb') as file:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(file.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(part)

        context = ssl._create_unverified_context()
        
        with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
            try:
                server.login(self.username, self.password)
                server.sendmail(self.sender, self.receiver, msg.as_string())
            except smtplib.SMTPAuthenticationError as serr:
                print("Isn't working because ", serr)

