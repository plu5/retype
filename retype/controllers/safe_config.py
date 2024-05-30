import os
import json
import logging
from copy import deepcopy

from retype.constants import default_config
from retype.extras.dict import SafeDict

logger = logging.getLogger(__name__)


class SafeConfig:
    def __init__(self):
        self.config_rel_path = 'config.json'
        self.default_user_dir = default_config['user_dir']
        self.base_config_abs_path = os.path.join(
            self.default_user_dir, self.config_rel_path)
        self.config = self.raw = self.load(self.base_config_abs_path)
        self.safe_dict = SafeDict(self.config, default_config,
                                  ['rdict', 'sdict', 'kdict'])

    def isPathDefaultUserDir(self, path):
        return os.path.abspath(path) == \
            os.path.abspath(self.default_user_dir)

    def load(self, path):
        config = self._load(path)
        user_dir = config['user_dir'] if config else None
        if user_dir and not self.isPathDefaultUserDir(user_dir):
            custom_path = os.path.join(user_dir, self.config_rel_path)
            logger.debug("Non-default user_dir: {}\n\
Attempting to load config from: {}".format(user_dir, custom_path))
            config = self._load(custom_path)
            if not config:
                config = deepcopy(default_config)
                config['user_dir'] = user_dir
                return config
        return config or default_config

    def _load(self, path):
        if os.path.exists(path):
            logger.info(f'Read config: {path}')
            with open(path, 'r') as f:
                config = json.load(f)
                return config
        else:
            logger.debug(
                f'Config path {path} not found.\n'
                'This is normal if the config file has not been created yet.')

    def populate(self, config_dict):
        self.config = self.raw = config_dict
        self.safe_dict.raw = self.raw

    def save(self):
        user_dir = self.raw['user_dir']
        if not os.path.exists(user_dir):
            logger.error(f'Unable to find user_dir {user_dir}')
            return

        path = os.path.join(user_dir, self.config_rel_path)
        with open(path, 'w') as f:
            json.dump(self.raw, f, indent=2)
        if not self.isPathDefaultUserDir(user_dir):
            path = os.path.join(self.default_user_dir, self.config_rel_path)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    dconfig = json.load(f)
                    dconfig['user_dir'] = user_dir
                with open(path, 'w') as f:
                    json.dump(dconfig, f, indent=2)
            else:
                logger.error(f'Unable to find dconfig {path}')

    def __getitem__(self, key, default=None):
        return self.safe_dict.__getitem__(key, default)

    def get(self, key, default=None):
        return self.__getitem__(key, default)
