from xmlrpc.client import Server
from .psmb import Client
from .handler import broadcast
from mcdreforged.api.all import PluginServerInterface, event_listener, ServerInterface, Info, new_thread
from .config import load_config, Config
import asyncio 
client: Client
config: Config


def on_load(server: PluginServerInterface, old):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # 初始化pypsmb
    global client, config
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

@new_thread('psmb msg publish')
def publish(msg):
    asyncio.run(client.publish(msg))


@event_listener('more_apis.death_message')
def _(server: ServerInterface, msg):
    # 悲报
    # TODO 这个悲报应该Build成数据包，再发
    publish(msg)
    pass

@event_listener('more_apis.player_made_advancement')
def _(server: ServerInterface, advancement):
    # 喜报
    pass

@event_listener('more_apis.server_crashed')
def _(server: ServerInterface, crash_path):
    pass

@event_listener('mcdr.user_info')
def _(server: PluginServerInterface, info: Info):
    
    pass