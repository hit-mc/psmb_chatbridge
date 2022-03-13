# 包含若干事件监听器，负责将事件打包并交给publish发送。
# 另外还有初始化连接协议的责任
import asyncio
import threading

from mcdreforged.api.all import PluginServerInterface, event_listener, ServerInterface, Info
from hitmc_messages import (Message,
                            MessageType,
                            PlayerChatMessage,
                            PlayerDeathMessage,
                            Dispatcher,
                            PlayerMessage)
from loguru import logger
from .config import load_config, Config
from .handler import MCServerBroadcaster
from psmb_client.guardian import SyncGuardian


dispatcher: Dispatcher

client: SyncGuardian
config: Config
base_msg: Message  # 带有client_id client_name 的基础消息
broadcaster: MCServerBroadcaster


async def feed_packet(packet: bytes):
    dispatcher.feed_packet(packet)


def on_load(server: PluginServerInterface, old):
    # 初始化pypsmb
    global client, config, base_msg, broadcaster, dispatcher
    dispatcher = Dispatcher()
    path = server.get_data_folder()
    config = load_config(path)
    base_msg = Message(client_name=config.client_name,
                       client_id=config.client_id,
                       msg_type=MessageType.PLAYER_CHAT,
                       content='')
    client = SyncGuardian(config.psmb_host,
                          config.psmb_port,
                          config.psmb_topic,
                          config.client_id,
                          feed_packet)
    broadcaster = MCServerBroadcaster(
        server,
        config.client_id,
        config.client_name,
        dispatcher,
        base_msg,
        client)
    logger.info('Connecting to psmb server.')
    client.start()


def death_msg(server, player_name, index, msg):
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
    # new_thread 这个装饰器类型提示不好使，会导致Pylance出错
    client.send_msg(resp_model.json(), 5)


def on_unload(server: PluginServerInterface):
    try:
        client.close(5)
    except NameError:
        pass


@event_listener('more_apis.death_message')
def _(server: ServerInterface, index: int, msg: str, player_name: str | None):
    # 悲报
    if player_name is not None:
        threading.Thread(target=death_msg, args=(
            server, player_name, index, msg), name='Death MSG').start()
    else:
        # 没玩家名字？没道理啊，先抛异常吧
        raise NotImplementedError("Nobody dead?")


@event_listener('more_apis.player_made_advancement')
def _(server: ServerInterface, advancement: str | None):
    # 喜报
    if advancement is None:
        return
    resp_model = PlayerMessage(**base_msg.dict(), player_name='')
    resp_model.content = advancement
    resp_model.msg_type = MessageType.PLAYER_ADVANCEMENT
    threading.Thread(target=client.send_msg,
                     args=(resp_model.json(), 5)).start()

@event_listener('mcdr.user_info')
def _(server: PluginServerInterface, info: Info):
    if info.player is not None:
        resp_model = PlayerChatMessage(**base_msg.dict(),
                                       player_name=info.player)
        resp_model.content = info.content if info.content is not None else ''
        resp_model.msg_type = MessageType.PLAYER_CHAT
        threading.Thread(target=client.send_msg,
                         args=(resp_model.json(), 5)).start()
    else:
        print(info.content)


@event_listener('mcdr.player_joined')
def _(server: PluginServerInterface, player: str, info: Info):
    resp_model = PlayerMessage(**base_msg.dict(),
                               player_name=player)
    resp_model.content = info.content if info.content is not None else ''
    resp_model.msg_type = MessageType.PLAYER_JOIN
    threading.Thread(target=client.send_msg,
                     args=(resp_model.json(), 5)).start()


@event_listener('mcdr.player_left')
def _(server: PluginServerInterface, player: str):
    resp_model = PlayerMessage(**base_msg.dict(),
                               player_name=player)
    resp_model.msg_type = MessageType.PLAYER_LEAVE
    threading.Thread(target=client.send_msg,
                     args=(resp_model.json(), 5)).start()
