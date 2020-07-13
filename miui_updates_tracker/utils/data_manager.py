"""
MIUI Updates Tracker Data Management class
"""
from glob import glob
from pathlib import Path
from shutil import copyfile

import yaml


class DataManager:
    """
    DataManager class is responsible for managing all data storing, loading, and backing up tasks.

    :attr: `data`: a dictionary of the data
    :attr: `file`: the file containing the data path.
    :attr: `backup_file`: the backup file path.
    :meth: `save` a wrapper function to call `write_file` method with `data` and `file` parameters.`
    :meth: `write_file` A method that writes the data to YAML file.
    :meth: `read_file` A method that reads the data from YAML file.
    :meth: `backup` A method for backing up the `file` into `backup_file`.
    :meth: `backup_all` A method for backing up all files in `file` parent directory.
    """

    def __init__(self, data: dict, file):
        """
        DataManager constructor
        :param data: date that will be stored
        :param file: file that will be used to store data
        """
        self.data: dict = data
        self.file: Path = Path(file)
        self.backup_file: Path = Path(f"{self.file}.bak")
        if not self.file.exists():
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.file.touch()

    def save(self):
        """
        Saves the data into the file
        :return:
        """
        self.write_file(self.file, self.data)

    @staticmethod
    def write_file(file, data):
        """Write data into the file"""
        with open(f"{file}", "w", encoding="utf-8") as out:
            yaml.dump(data, out, allow_unicode=True)

    @staticmethod
    def read_file(file):
        """Read data from the file"""
        with open(file, "r") as yaml_file:
            return yaml.load(yaml_file, yaml.FullLoader)

    def backup(self):
        """Backup the file up (copy current to backup one)"""
        copyfile(self.file, self.backup_file)
        return self.backup_file

    @staticmethod
    def backup_all(directory):
        """Iterate through all files in a directory and backup them"""
        for item in glob(directory):
            copyfile(f"{item}", f"{item}.bak")
