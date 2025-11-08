"""Load balancing module"""
import random
from typing import Optional
from ..core.models import Token
from ..core.config import config
from .token_manager import TokenManager
from .token_lock import TokenLock

class LoadBalancer:
    """Token load balancer with random selection and image generation lock"""

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        # Use image timeout from config as lock timeout
        self.token_lock = TokenLock(lock_timeout=config.image_timeout)

    async def select_token(self, for_image_generation: bool = False) -> Optional[Token]:
        """
        Select a token using random load balancing

        Args:
            for_image_generation: If True, only select tokens that are not locked for image generation

        Returns:
            Selected token or None if no available tokens
        """
        active_tokens = await self.token_manager.get_active_tokens()

        if not active_tokens:
            return None

        # If for image generation, filter out locked tokens
        if for_image_generation:
            available_tokens = []
            for token in active_tokens:
                if not await self.token_lock.is_locked(token.id):
                    available_tokens.append(token)

            if not available_tokens:
                return None

            # Random selection from available tokens
            return random.choice(available_tokens)
        else:
            # For video generation, no lock needed
            return random.choice(active_tokens)
