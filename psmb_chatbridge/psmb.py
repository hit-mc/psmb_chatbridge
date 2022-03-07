from .pypsmb_client import SubscribeProtocol, PublishProtocol
import asyncio
from mcdreforged.api.all import new_thread
from typing import Any
from typing import Callable
from .errors import ClientNotAvailableError


class Client:

    def __init__(self,
                 host: str,
                 port: int,
                 enable_ssl: bool,
                 pub_topic: str,
                 sub_id_pattern: str,
                 sub_id: int,
                 *handlers: Callable[[bytes], Any]):
        self.host = host
        self.port = port
        self.enable_ssl = enable_ssl
        self.pub_topic = pub_topic
        self.sub_id_pattern = sub_id_pattern
        self.sub_id = sub_id
        self.handlers = handlers

    async def _pub(self) -> None:
        on_con_lost = asyncio.Future()
        on_exchange_ready = asyncio.Event()
        transport, protocol = await self.loop.create_connection(
            lambda: PublishProtocol(
                topic=self.pub_topic,
                on_con_lost=on_con_lost,
                exchange_ready=on_exchange_ready),
            host=self.host,
            port=self.port,
            ssl=self.enable_ssl)
        await on_exchange_ready.wait()
        self.pub_transport = transport
        self.pub_protocol = protocol

    async def _sub(self) -> None:
        on_con_lost = asyncio.Future()
        on_exchange_ready = asyncio.Event()
        transport, protocol = await self.loop.create_connection(
            lambda: SubscribeProtocol(self.sub_id_pattern, *self.handlers,
                                      subscriber_id=self.sub_id,
                                      on_con_lost=on_con_lost,
                                      exchange_ready=on_exchange_ready),
            host=self.host,
            port=self.port,
            ssl=self.enable_ssl
        )
        await on_exchange_ready.wait()
        self.sub_transport = transport
        self.sub_protocol = protocol

    @new_thread('psmb client establish')
    def establish(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        self.pub_task = loop.create_task(self._pub())
        self.sub_task = loop.create_task(self._sub())
        loop.run_forever()

    def close(self):
        self.pub_transport.write(b'BYE')
        self.sub_transport.write(b'BYE')
        # Subscriber协议本不应如此，但如果不这么写的话，PSMB Server可能不会主动断开连接？
        self.pub_transport.close()
        self.sub_transport.close()
        self.loop.stop()
        # self.loop.close()

    async def publish(self, msg):
        if not self.pub_task.done():
            raise ClientNotAvailableError(
                "Connection for publishing is not available now.")
        if not self.sub_task.done():
            raise ClientNotAvailableError(
                "Connection for subscription is not available now.")
        await self.pub_protocol.send_msg(msg)
