"""
Módulo PubSub para manejar publicaciones de eventos en tiempo real usando Redis.
"""
import json
import os
from typing import Any, Dict
from redis import asyncio as aioredis


class PubSub:
    """Cliente PubSub para publicar eventos en Redis"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self._redis = None
    
    async def get_redis(self):
        """Obtener conexión a Redis"""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url, 
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """
        Publicar un mensaje en un canal de Redis
        
        Args:
            channel: Nombre del canal
            message: Mensaje a publicar (será serializado a JSON)
        """
        try:
            redis = await self.get_redis()
            await redis.publish(channel, json.dumps(message))
        except Exception as e:
            print(f"Error publishing to Redis channel {channel}: {e}")
    
    async def close(self):
        """Cerrar la conexión a Redis"""
        if self._redis:
            await self._redis.close()


async def publish_plan_update(pubsub: PubSub, plan_id: str, data: Dict[str, Any]):
    """
    Publicar actualización de un plan
    
    Args:
        pubsub: Instancia de PubSub
        plan_id: ID del plan
        data: Datos de la actualización
    """
    channel = f"plan_update:{plan_id}"
    message = {
        "type": "plan_update",
        "plan_id": plan_id,
        "data": data
    }
    await pubsub.publish(channel, message)


async def publish_invitation(pubsub: PubSub, invitation_id: str, data: Dict[str, Any]):
    """
    Publicar evento de invitación
    
    Args:
        pubsub: Instancia de PubSub
        invitation_id: ID de la invitación
        data: Datos de la invitación
    """
    channel = f"invitation:{invitation_id}"
    message = {
        "type": "invitation",
        "invitation_id": invitation_id,
        "data": data
    }
    await pubsub.publish(channel, message)


async def publish_progress(pubsub: PubSub, plan_id: str, data: Dict[str, Any]):
    """
    Publicar progreso de un plan
    
    Args:
        pubsub: Instancia de PubSub
        plan_id: ID del plan
        data: Datos del progreso
    """
    channel = f"plan_progress:{plan_id}"
    message = {
        "type": "progress",
        "plan_id": plan_id,
        "data": data
    }
    await pubsub.publish(channel, message)
