import logging
import traceback
from channelsmultiplexer import AsyncJsonWebsocketDemultiplexer
from authentication.consumers import JWTTokenConsumer
from users.consumers import LoggedUserConsumer

logger = logging.getLogger(__name__)


class AppApplicationDemultiplexer(AsyncJsonWebsocketDemultiplexer):
    applications = {
        "token": JWTTokenConsumer.as_asgi(),
        "user": LoggedUserConsumer.as_asgi(),
    }

    async def connect(self):
        """Handle WebSocket connection"""
        try:
            user = self.scope.get("user")
            logger.info(
                f"WebSocket connecting for user: {getattr(user, 'id', 'anonymous')}"
            )
            await super().connect()
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {traceback.format_exc()}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection properly"""
        try:
            user = self.scope.get("user")
            logger.info(
                f"WebSocket disconnecting for user: {getattr(user, 'id', 'anonymous')} with code: {close_code}"
            )
            await super().disconnect(close_code)
        except Exception as e:
            logger.error(
                f"Error during WebSocket disconnection: {traceback.format_exc()}"
            )

    async def receive_json(self, content, **kwargs):
        """Log para identificar streams não mapeados"""
        stream = content.get("stream")
        if stream and stream not in self.applications:
            logger.error(
                f"🚨 STREAM NÃO MAPEADO: '{stream}' - Streams disponíveis: {list(self.applications.keys())}"
            )
            logger.error(f"📄 Conteúdo da mensagem: {content}")

        try:
            return await super().receive_json(content, **kwargs)
        except Exception as e:
            logger.error(
                f"Error during WebSocket receive_json: {traceback.format_exc()}"
            )
            logger.error(f"Content: {content}")
            logger.error(f"Scope: {self.scope}")
            logger.error(f"Kwargs: {kwargs}")

            return await self.close(code=4000)
