# 包含若干事件监听器，负责将事件打包并交给publish发送。
# 另外还有初始化连接协议的责任
from .psmb import Client
from .handler import MCServerBroadcaster
from mcdreforged.api.all import PluginServerInterface, event_listener, ServerInterface, Info, new_thread
from .config import load_config, Config
import asyncio
from .message import Message, MessageType, PlayerChatMessage, PlayerDeathMessage
client: Client
config: Config
base_msg: Message  # 带有client_id client_name 的基础消息
broadcaster: MCServerBroadcaster


def on_load(server: PluginServerInterface, old):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # 初始化pypsmb
    global client, config, base_msg, broadcaster
    path = server.get_data_folder()
    config = load_config(path)

    broadcaster = MCServerBroadcaster(
        server, config.client_id, config.client_name)
    client = Client(config.psmb_host,
                    config.psmb_port,
                    config.psmb_enable_tls,
                    config.psmb_pub_topic,
                    config.psmb_sub_id_pattern,
                    config.client_id,
                    broadcaster.broadcast)
    client.establish()
    base_msg = Message(client_name=config.client_name,
                       client_id=config.client_id, msg_type=MessageType.PLAYER_CHAT, content='')


def on_unload(server: PluginServerInterface):
    try:
        client.close()
    except NameError:
        pass


@new_thread('psmb msg publish')
def publish(msg):
    asyncio.run(client.publish(msg))


@new_thread('psmb death message')
def death_message(server: ServerInterface, index: int, msg: str, player_name: str | None):
    if player_name is not None:
        api = server.get_plugin_instance('minecraft_data_api')
        pos = api.get_player_coordinate(player_name)
        resp_model = PlayerDeathMessage(**base_msg.dict(),
                                        death_position=(pos.x, pos.y, pos.z),
                                        death_dim=api.get_player_dimension(
                                            player_name),
                                        player_name=player_name,
                                        index=index)
        resp_model.content = msg
        resp_model.msg_type = MessageType.PLAYER_DEATH
        publish(resp_model.json())  # new_thread 这个装饰器类型提示不好使，会导致Pylance出错
    else:
        # 没玩家名字？没道理啊，先抛异常吧
        raise NotImplementedError("Nobody dead?")


@new_thread('psmb player chat')
def player_chat(server: ServerInterface, msg: str, player_name: str):
    resp_model = PlayerChatMessage(**base_msg.dict(),
                                   player_name=player_name)
    resp_model.content = msg
    resp_model.msg_type = MessageType.PLAYER_CHAT
    publish(resp_model.json())  # new_thread
    pass


@event_listener('more_apis.death_message')
def _(server: ServerInterface, index: int, msg: str, player_name: str | None):
    # 悲报
    death_message(server, index, msg, player_name)  # 还是 new_thread


@event_listener('more_apis.player_made_advancement')
def _(server: ServerInterface, advancement):
    # 喜报
    pass


@event_listener('mcdr.user_info')
def _(server: PluginServerInterface, info: Info):
    if info.player is not None:
        player_chat(server, info.content, info.player)
    else:
        print(info.content)