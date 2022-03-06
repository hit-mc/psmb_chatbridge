import enum
from typing import Tuple
from pydantic import BaseModel

class MessageType(enum.Enum):
    PLAYER_DEATH = 1
    SERVER_CRASHED = 2
    PLAYER_CHAT = 3
    PLAYER_ADVANCEMENT = 4


class Message(BaseModel):
    client_name: str
    client_id: int
    msg_type: MessageType
    content: str

class PlayerMessage(Message):
    player_name: str

class PlayerDeathMessage(PlayerMessage):
    death_position: Tuple[float, float, float]
    death_dim: int # Dim ID

class PlayerAdvancementMessage(PlayerMessage):
    pass


class PlayerServerChatMessage(PlayerMessage):
    pass

class ServerCrashedMessage(Message):
    pass
