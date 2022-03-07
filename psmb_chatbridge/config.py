from distutils.command.config import config
from pydantic import BaseModel
import os.path
import os


class _PSMBConfig(BaseModel):
    psmb_host: str = '127.0.0.1'
    psmb_port: int = 1234
    psmb_pub_topic: str = 's2q'
    psmb_sub_id_pattern: str = 'q2s'
    psmb_enable_tls: bool = False
    client_id: int = 3  # Client ID 用这个来区分是否为自己
    enable_tls: bool = False # 启用TLS


class Config(_PSMBConfig):
    client_name: str  # 你的某一个子服的名字，例如survival creative mirror


def load_config(path: str) -> Config:
    config_path = os.path.join(path, 'config.json')
    if not os.path.exists(config_path):
        # Generate skeleton file
        with open(config_path, 'w') as f:
            d = Config(client_name='survival')
            f.write(d.json())
        raise RuntimeError("No config file. Generated a schema config.")
    return Config.parse_file(config_path)
