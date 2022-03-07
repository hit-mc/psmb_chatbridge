from .message import *
from mcdreforged.api.all import ServerInterface
class MCServerBroadcaster:
    
    def __init__(self, server: ServerInterface, client_id: int) -> None:
        self.server: ServerInterface = server
        self.client_id = client_id

    def broadcast(self, raw_msg: bytes):
        """这是一个消息处理函数，把消息发给MC所有玩家

        Args:
            msg (str): 要发送的消息
        """
        msg = str(raw_msg, encoding='UTF-8')
        # parse msg to obj here
        r = Message.parse_raw(msg)
        if r.client_id == self.client_id:
            if r.msg_type == MessageType.PLAYER_DEATH:
                p = PlayerDeathMessage.parse_raw(msg)
                # TODO 让这个坐标可以用小地图点
                self.server.broadcast('[x: %.3f, y: %.3f, z: %.3f]' % p.death_position)
            return
        self.server.broadcast(msg)