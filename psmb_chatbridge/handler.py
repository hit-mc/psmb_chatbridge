import threading
from typing import Optional, Tuple, List
from loguru import logger
from mcdreforged.api.all import ServerInterface, RTextList, RText, RColor
from hitmc_messages import (MessageType,
                            Message,
                            PlayerDeathMessage,
                            PlayerChatMessage,
                            PlayerListResponseMessage,
                            PlayerMessage,
                            Dispatcher)
from psmb_client.guardian import SyncGuardian

from .location_rtext import location
from .location_rtext.position import Position


class MCServerBroadcaster:

    def __init__(self, server: ServerInterface, client_id: int, client_name: str, dispatcher: Dispatcher, base_msg: Message, client: SyncGuardian) -> None:
        self._server: ServerInterface = server
        self._client_id = client_id
        self._client_name = client_name
        self._dispatcher = dispatcher
        self._base_msg = base_msg
        self._client = client
        self._dispatcher.add_message_listener(
            MessageType.PLAYER_CHAT, self.player_chat)
        self._dispatcher.add_message_listener(
            MessageType.PLAYER_DEATH, self.player_death)
        self._dispatcher.add_message_listener(
            MessageType.PLAYER_JOIN, self.player_join)
        self._dispatcher.add_message_listener(
            MessageType.PLAYER_LEAVE, self.player_left)
        self._dispatcher.add_message_listener(
            MessageType.PLAYER_LIST_REQUEST, self.player_list)
        self._dispatcher.add_message_listener(
            MessageType.SERVER_PING, self.server_ping)

    @staticmethod
    def rdeath(msg: PlayerDeathMessage) -> RTextList:
        return location(msg.player_name, position=Position.fromTuple(msg.death_position), dimension_str=str(msg.death_dim))

    @staticmethod
    def rchat(msg: PlayerChatMessage) -> RTextList:
        return RTextList(RText('[{}]'.format(msg.client_name), color=RColor.aqua),
                         RText('<{}>'.format(msg.player_name), RColor.dark_aqua),
                         RText(msg.content, RColor.white))

    @staticmethod
    def rjoin(msg: PlayerMessage) -> RTextList:
        return RTextList(RText('[{}]'.format(msg.client_name), color=RColor.aqua),
                         RText('{}'.format(msg.player_name), RColor.dark_aqua),
                         RText(" joined the game", RColor.white))

    @staticmethod
    def rleft(msg: PlayerMessage) -> RTextList:
        return RTextList(RText('[{}]'.format(msg.client_name), color=RColor.aqua),
                         RText('{}'.format(msg.player_name), RColor.dark_aqua),
                         RText(" left the game", RColor.white))

    def player_chat(self, msg: PlayerChatMessage):
        if msg.client_id != self._client_id:
            self._server.broadcast(self.rchat(msg))

    def player_death(self, msg: PlayerDeathMessage):
        if msg.client_id == self._client_id:
            self._server.broadcast(self.rdeath(msg))

    def player_join(self, msg: PlayerMessage):
        if msg.client_id != self._client_id:
            self._server.broadcast(self.rjoin(msg))

    def player_left(self, msg: PlayerMessage):
        if msg.client_id != self._client_id:
            self._server.broadcast(self.rleft(msg))

    def _player_list(self):
        # Server List 请求不可能自己发出
        api = self._server.get_plugin_instance('minecraft_data_api')
        result = api.get_server_player_list()  # type: ignore
        result: Optional[Tuple[int, int, List[str]]]
        if result is None:
            return
        _, _, player_list = result
        resp_model = PlayerListResponseMessage(**self._base_msg.dict(),
                                               online_players=player_list)
        resp_model.msg_type = MessageType.PLAYER_LIST_RESPONSE
        threading.Thread(target=self._client.send_msg,
                         args=(resp_model.json(), 5)).start()

    def player_list(self, msg: Message):
        threading.Thread(target=self._player_list).start()

    def server_ping(self, msg: Message):
        resp_model = Message(**self._base_msg.dict())
        resp_model.msg_type = MessageType.SERVER_PONG
        threading.Thread(target=self._client.send_msg(
            resp_model.json(), 5)).start()
