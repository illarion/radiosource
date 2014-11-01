import ConfigParser
from ConfigParser import NoOptionError

__author__ = 'shaman'


class Config(object):
    locations = ('/etc/radiosource/radiosource.conf',
                 '/etc/radiosource.conf',
                 'radiosource.conf'
    )

    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read(Config.locations)
        self.config = config

    def set_mock_config(self, config_parser_object):
        self.config = config_parser_object

    def get(self, section, option, default=None):
        try:
            result = self.config.get(section, option)
        except NoOptionError:
            return default

        return result

    def get_boolean(self, section, option, default=None):
        try:
            result = self.config.getboolean(section, option)
        except NoOptionError:
            return default

        return result

    def is_present(self, section, option):
        try:
            self.config.get(section, option)
        except NoOptionError:
            return False

        return True
