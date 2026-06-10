import os
import json
import logging
import traceback
from copy import deepcopy
from qt import QMessageBox

from typing import TYPE_CHECKING

from retype.extras.dict import SafeDict
from retype.constants import default_config

logger = logging.getLogger(__name__)


class _SafeConfig:
    def __init__(self):
        # type: (_SafeConfig) -> None
        self.config_rel_path = 'config.json'
        self.default_user_dir = default_config['user_dir']
        self.base_config_abs_path = os.path.join(
            self.default_user_dir, self.config_rel_path)
        self.config = self.raw = self.load(self.base_config_abs_path)
        self.safe_dict = SafeDict(
            self.config, default_config,
            ['rdict', 'sdict', 'kdict'])

    def isPathDefaultUserDir(self, path):
        # type: (_SafeConfig, str) -> bool
        return os.path.abspath(path) == \
            os.path.abspath(self.default_user_dir)

    def load(self, path):
        # type: (_SafeConfig, str) -> Config
        config = self._load(path)
        if config is None:      # Loading failed
            # Nothing modifies it, but may as well explicitly avoid mutation
            return deepcopy(default_config)

        user_dir = config['user_dir']
        if user_dir and not self.isPathDefaultUserDir(user_dir):
            custom_path = os.path.join(user_dir, self.config_rel_path)
            logger.debug("Non-default user_dir: {}\n\
Attempting to load config from: {}".format(user_dir, custom_path))
            config = self._load(custom_path)
            if not config:
                config = deepcopy(default_config)
                config['user_dir'] = user_dir
        return config

    def _load(self, path):
        # type: (_SafeConfig, str) -> Config | None
        if os.path.exists(path):
            logger.info(f'Read config: {path}')
            try:
                with open(path, 'r') as f:
                    config = json.load(f)  # type: Config
                    return config
            except OSError as e:
                s = 'Unable to read config file.'
                logger.error(f"{s}\n{e}", exc_info=True)
                msg = QMessageBox(QMessageBox.Icon.Warning, 'retype', s)
                msg.setDetailedText(f'Path: {path}\n\n'
                                    f'{traceback.format_exc()}')
                msg.exec()
        else:
            logger.debug(
                f'Config path {path} not found.\n'
                'This is normal if the config file has not been created yet.')
            return None

    def populate(self, config_dict):
        # type: (_SafeConfig, NestedDict) -> None
        self.config = self.raw = config_dict  # type: ignore[assignment]
        self.safe_dict.raw = self.raw  # type: ignore[assignment]

    def save(self):
        # type: (_SafeConfig) -> None
        user_dir = self.raw['user_dir']
        path = os.path.join(user_dir, self.config_rel_path)
        if not self._save(path, self.raw):  # Saving failed
            return

        if not self.isPathDefaultUserDir(user_dir):
            dconfig = self.loadDconfig()
            if dconfig is not None:
                dconfig['user_dir'] = user_dir
                self._save(path, dconfig)

    def _save(self, path, data):
        # type: (_SafeConfig, str, Config) -> bool
        try:
            with open(path, 'w') as f:
                logger.debug(f'Saving config: {path}')
                json.dump(data, f, indent=2)
        except OSError as e:
            s = 'Unable to save config file.'
            logger.error(f"{s}\n{e}", exc_info=True)
            msg = QMessageBox(QMessageBox.Icon.Warning, 'retype', s)
            msg.setDetailedText(f'Path: {path}\n\n'
                                f'{traceback.format_exc()}')
            msg.exec()
            return False
        return True

    def loadDconfig(self):
        # type: (_SafeConfig) -> Config | None
        dconfig = None
        path = os.path.join(self.default_user_dir, self.config_rel_path)
        try:
            with open(path, 'r') as f:
                dconfig = json.load(f)  # type: Config
        except OSError as e:
            s = 'Unable to load dconfig file.'
            logger.error(f"{s}\n{e}", exc_info=True)
            msg = QMessageBox(QMessageBox.Icon.Warning, 'retype', s)
            msg.setDetailedText(f'Path: {path}\n\n'
                                f'{traceback.format_exc()}')
            msg.exec()
        return dconfig

    def __getitem__(self, key, default=None):
        # type: (_SafeConfig, str, object | None) -> object
        return self.safe_dict.__getitem__(key, default)

    def get(self, key, default=None):
        # type: (_SafeConfig, str, object | None) -> object
        return self.__getitem__(key, default)


if TYPE_CHECKING:
    from retype.extras.metatypes import (  # noqa: F401
        Config, NestedDict, SConfig)
    SafeConfig = SConfig
else:
    SafeConfig = _SafeConfig
