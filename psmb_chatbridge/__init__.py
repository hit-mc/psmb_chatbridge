from .psmb import Client
from .handler import broadcast
from mcdreforged.api.all import PluginServerInterface, new_thread
from .config import load_config
import asyncio 
client: Client


def on_load(server: PluginServerInterface, old):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # 初始化pypsmb
    global connection_task, client
    path = server.get_data_folder()
    config = load_config(path)
    client = Client(config.psmb_host,
                    config.psmb_port,
                    config.psmb_enable_tls,
                    config.psmb_pub_topic,
                    config.psmb_sub_id_pattern,
                    config.psmb_subscriber_id,
                    broadcast)
    client.establish()



def on_unload(server: PluginServerInterface):
    client.close()