import asyncio
import socket
import struct
from typing import Callable
import asyncio.transports as transports
import enum


class ClientState(enum.Enum):
    HANDSHAKING = 1
    MODE_CHOOSING_START = 2
    MODE_CHOOSING_PENDING = 3
    MSG_EXCHANGING = 4


class SubscriberOptions(enum.Enum):
    ALLOW_HISTORY = 1


class PSMBHandshakeProtocol(asyncio.Protocol):
    _protocol_version = 1

    def __init__(self, on_con_lost: asyncio.Future, exchange_ready):
        self.on_con_lost = on_con_lost
        self.exchange_ready = exchange_ready
        self.state = ClientState.HANDSHAKING

    def connection_made(self, transport: transports.Transport) -> None:
        self._transport = transport
        if self.state == ClientState.HANDSHAKING:
            transport.write(b'PSMB')
            transport.write(struct.pack(
                'I', socket.htonl(self._protocol_version)))
            transport.write(b'\x00\x00\x00\x00')
        return super().connection_made(transport)

    def data_received(self, data: bytes) -> None:
        if self.state == ClientState.HANDSHAKING:
            if data[:2] != b'OK':
                raise NotImplementedError('')
            else:
                # 切换状态到模式选择
                self.state = ClientState.MODE_CHOOSING_START
        return super().data_received(data)

    def connection_lost(self, exc: Exception | None) -> None:
        self.on_con_lost.set_result(True)
        return super().connection_lost(exc)


class PublishProtocol(PSMBHandshakeProtocol):
    def __init__(self, topic, on_con_lost: asyncio.Future, exchange_ready: asyncio.Event):
        super().__init__(on_con_lost, exchange_ready)
        self.topic = topic

    async def _nop(self):
        while True:
            await asyncio.sleep(15)
            self._transport.write(b"NOP")

    def data_received(self, data: bytes) -> None:
        super().data_received(data)
        if self.state == ClientState.MODE_CHOOSING_START:
            # 开始选择模式，这里需要选广播
            self._transport.write(b'PUB')
            self._transport.write(self.topic.encode(encoding='ascii'))
            self._transport.write(b'\0')
            self.state = ClientState.MODE_CHOOSING_PENDING  # 切换到等待服务器结果状态
        elif self.state == ClientState.MODE_CHOOSING_PENDING:
            if data[:2] != b'OK':
                raise NotImplementedError('')
            else:
                self.state = ClientState.MSG_EXCHANGING
                self.exchange_ready.set()
                loop = asyncio.get_event_loop()
                self.nop_task = loop.create_task(self._nop())

    def connection_lost(self, exc: Exception | None) -> None:
        super().connection_lost(exc)
        self.nop_task.cancel()

    async def send_msg(self, *msg_list: str):
        assert self.state == ClientState.MSG_EXCHANGING
        for msg in msg_list:
            self._transport.write(b'MSG')
            data = msg.encode(encoding='UTF-8')
            self._transport.write(len(data).to_bytes(8, 'big'))
            self._transport.write(data)

    async def send_nop(self) -> None:
        self._transport.write(b"NOP")


class SubscribeProtocol(PSMBHandshakeProtocol):
    def __init__(self, id_pattern: str, *handlers: Callable[[bytes], None], subscriber_id: int | None = None, on_con_lost: asyncio.Future, exchange_ready: asyncio.Event):
        super().__init__(on_con_lost, exchange_ready)
        self.id_pattern = id_pattern
        self.handlers = handlers
        self._command_buffer = bytearray()
        self.subscriber_id = subscriber_id

    def on_nop(self):
        self._transport.write(b'NIL')

    def on_bye(self):
        self._transport.close()

    def data_received(self, data: bytes) -> None:
        super().data_received(data)
        if self.state == ClientState.MODE_CHOOSING_START:
            # 开始选择模式，这里需要选订阅
            self._transport.write(b'SUB')
            option = (
                SubscriberOptions.ALLOW_HISTORY.value) if self.subscriber_id is not None else 0
            self._transport.write(option.to_bytes(4, 'big'))
            self._transport.write(self.id_pattern.encode('UTF-8'))
            self._transport.write(b'\0')
            if self.subscriber_id is not None:
                self._transport.write(self.subscriber_id.to_bytes(8, 'big'))
            self.state = ClientState.MODE_CHOOSING_PENDING
        elif self.state == ClientState.MODE_CHOOSING_PENDING:
            if data[:2] != b'OK':
                raise NotImplementedError('')
            else:
                self.state = ClientState.MSG_EXCHANGING
                self.exchange_ready.set()
        elif self.state == ClientState.MSG_EXCHANGING:
            self._exchange_data(data)

    def _exchange_data(self, data: bytes):
        command_len = 3
        number_len = 8
        self._command_buffer.extend(data)
        if len(self._command_buffer) >= 3:
            c = self._command_buffer[:3]
            if c == b'NOP':
                self.on_nop()
                self._command_buffer = self._command_buffer[command_len:]
            elif c == b'BYE':
                self.on_bye()
                self._command_buffer = self._command_buffer[command_len:]
            elif c == b'MSG':
                # Try to decode message pack
                offset = command_len + number_len
                if len(self._command_buffer) >= offset:
                    msg_len = int.from_bytes(
                        self._command_buffer[command_len: offset], 'big')
                    n = offset + msg_len
                    if len(self._command_buffer) >= n:
                        for handler in self.handlers:
                            handler(self._command_buffer[offset:])
                        self._command_buffer = self._command_buffer[n:]
