from datetime import datetime, date, timedelta
import os
import yaml

# FIXME change logger to fit yaml config file

levels = ["DEBUG", "RUN", "WARNING", "ERROR", "CRITICAL"]

class Logger:
    _level = ""
    _date_format = ""
    _root_dir = ""
    _filedir = ""
    _curr_fileline = 1
    _logsize = 0

    def __new__(cls, rdir, level, dtformat=None, logsize=3000):
        
        if level not in levels:
            print("CRITICAL: Unknown Logger Level")
            return

        instance = super().__new__(cls)
        return instance

    def __init__(self, rdir, level, dtformat=None, logsize=3000) -> None:
        self._root_dir = rdir
        self._logsize = logsize
        self._filedir = self._get_filepath()
        self.config_file = os.path.join(self._root_dir, "settings", "config.yaml")
        with open(self.config_file, 'r') as file:
            self.config = yaml.load(file, yaml.SafeLoader)
        if dtformat == None:
            dtformat = self.config['options']['dateformat']

        self._level = level
        
        match dtformat:
            case 'EU':
                self._date_format = r"%d/%m/%Y [%H:%M:%S] | "
            case 'EU-ISO':
                self._date_format = r"%Y-%m-%d [%H:%M:%S] | "
            case 'US':
                self._date_format = r"%b %d, %Y [%I:%M:%S %p] | "
            case _:
                self._date_format = r"%d/%m/%Y [%H:%M:%S] | "

    def _get_filepath(self) -> str:
        # check what logfiles for current date exist and return path to the new one
        # by incrementing up to logfile_[date]-999.log
        today = date.today()
        d_formatted = today.strftime("%d_%m_%Y")

        for h in range(0, 10):
            for t in range(0, 10):
                for d in range(0, 10):
                    path = os.path.join(self._root_dir, "debug", f"logfile_{d_formatted}-{h}{t}{d}.log")

                    if not os.path.exists(path):
                        # create new logfile
                        with open(path, "x") as _:
                            pass
                        self._curr_fileline = 1
                        return path

    def log(self, message, level="RUN"):
        dtnow = datetime.now()
        tsnow = datetime.timestamp(dtnow)
        formatted_date = datetime.now().strftime(self._date_format)

        # if estimate is divisible by 1k or is over logsize check the real file length
        if self._curr_fileline%1000 == 0 or self._curr_fileline >= self._logsize or self._curr_fileline <= 1:
            # file read in binary for slight boost on opening time
            with open(self._filedir, "rb") as f:

                num_lines = sum(1 for _ in f)
                # update line count with real file line count
                # plus one to account for file starting line 1 (istead of 0)
                self._curr_fileline = num_lines + 1
                
                # if real fileline count is greater than logsize, create new logfile
                # and reset estimate to line 1
                if self._curr_fileline > self._logsize:
                    self._curr_fileline = 1
                    self._filedir = self._get_filepath()

        # increment rought estimate of on which file in line logger currently is
        self._curr_fileline += 1
   
        with open(self._filedir, "a+") as file:

            if level not in levels:
                file.seek(0)
                data = file.read(10)
                if len(data) > 0:
                    file.write("\n")

                file.write("\n")
                file.write("-" * 10 + '\n')
                file.write("ERROR: Unknown Logger Level for message:\n")
                file.write(formatted_date + level + ' | ' + message + '\n')
                file.write("Timestamp: " + str(tsnow) + '\n')
                file.write("-" * 10 + '\n')
                return

            if levels.index(level) >= levels.index(self._level):
                file.seek(0)
                data = file.read(10)
                if len(data) > 0:
                    file.write('\n')

                file.write(formatted_date + level + ' | ' + message)
                return

    def clear_logs(self, days: int = 30) -> None:
        # clear logs older than specified number of days (default = 30)
        # has to be periodically called from the outside
        today = date.today()
        retention_border = today - timedelta(days=days)
        logs_dir = os.path.join(self._root_dir, "debug")

        for file in os.listdir(logs_dir):
            # only consider files with date and number in name
            if len(file) > 11:
                # strip everything except the date portion of name
                str_date = file.lstrip("logfile_").replace("_", "/")[0:-8]
                file_date = datetime.strptime(str_date, "%d/%m/%Y").date()
                if file_date < retention_border:
                    full_path = os.path.join(logs_dir, file)
                    print(full_path)
                    os.remove(full_path)