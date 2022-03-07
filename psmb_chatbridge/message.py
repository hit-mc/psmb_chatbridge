import enum
from typing import Tuple
from pydantic import BaseModel


class MessageType(enum.Enum):
    PLAYER_DEATH = 1
    PLAYER_CHAT = 2
    PLAYER_ADVANCEMENT = 3
    QQ_GROUP = 4


class Message(BaseModel):
    client_name: str
    client_id: int
    msg_type: MessageType
    content: str


class QQGroupMessage(Message):
    pass


class PlayerMessage(Message):
    player_name: str


class PlayerDeathMessage(PlayerMessage):
    index: int
    death_position: Tuple[float, float, float]
    death_dim: int  # Dim ID


class PlayerAdvancementMessage(PlayerMessage):
    pass


class PlayerChatMessage(PlayerMessage):
    pass


class ServerCrashedMessage(Message):
    pass
