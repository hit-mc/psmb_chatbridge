import os.path
import os
import json

from distutils.command.config import config
from loguru import logger
from pydantic import BaseModel


class _PSMBConfig(BaseModel):
    psmb_host: str = '127.0.0.1'
    psmb_port: int = 13880
    psmb_topic: str = 's2q'
    client_id: int = 3  # Client ID 用这个来区分是否为自己


class Config(_PSMBConfig):
    client_name: str  # 你的某一个子服的名字，例如survival creative mirror


def load_config(path: str) -> Config:
    config_path = os.path.join(path, 'config.json')
    # logger.debug("Logging config file from {}", config_path)
    if not os.path.exists(config_path):
        logger.warning("No config file. Generated one.")
        # Generate skeleton file
        with open(config_path, 'w') as f:
            d = Config(client_name='survival')
            f.write(json.dumps(json.loads(d.json()), indent=4))
    return Config.parse_file(config_path)
