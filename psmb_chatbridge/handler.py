from .message import *
from mcdreforged.api.all import ServerInterface, RText


class MCServerBroadcaster:

    def __init__(self, server: ServerInterface, client_id: int, client_name: str) -> None:
        self.server: ServerInterface = server
        self.client_id = client_id
        self.client_name = client_name

    def broadcast(self, raw_msg: bytes):
        """这是一个消息处理函数，把消息发给MC所有玩家

        Args:
            msg (str): 要发送的消息
        """
        msg_json = str(raw_msg, encoding='UTF-8')
        # parse msg to obj here
        msg = Message.parse_raw(msg_json)
        if msg.client_id == self.client_id:
            if msg.msg_type == MessageType.PLAYER_DEATH:
                p = PlayerDeathMessage.parse_raw(msg_json)
                self.server.broadcast(self.rdeath(p))
        else:
            # 消息来源并不是自己，可以考虑转发
            if msg.msg_type == MessageType.PLAYER_CHAT:
                # 是玩家聊天
                self.server.broadcast(msg.content)
            elif msg.msg_type == MessageType.PLAYER_DEATH:
                # 有玩家在别的服务器死亡
                # 这里，我们的策略为只提醒生存服务器中的死亡现象
                p = PlayerDeathMessage.parse_raw(msg_json)
                if self.client_name == 'survival':
                    # 即，client在mirror或者creative服务端运行，生存服务器有人死亡
                    self.server.broadcast(self.rdeath(p))
