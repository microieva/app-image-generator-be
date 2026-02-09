import signal
import asyncio
import logging
from typing import Callable, List
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

class ShutdownManager:
    def __init__(self):
        self.is_shutting_down = False
        self.cleanup_handlers: List[Callable] = []
        self._exit_stack = AsyncExitStack()
        logger.info("ShutdownManager initialized")
        
    def add_cleanup_handler(self, handler: Callable):
        if handler not in self.cleanup_handlers:
            self.cleanup_handlers.append(handler)
            logger.debug(f"Registered cleanup handler: {handler.__name__}")
        
    async def run_cleanup(self):
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        logger.info("Running cleanup handlers...")
        
        for handler in reversed(self.cleanup_handlers):
            try:
                logger.debug(f"Executing cleanup handler: {handler.__name__}")
                
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler)
                    
                logger.debug(f"Cleanup handler completed: {handler.__name__}")
                
            except Exception as e:
                logger.error(f"Cleanup handler {handler.__name__} failed: {e}")
        
        await self._exit_stack.aclose()
        logger.info("Cleanup completed")
    
    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.run_cleanup())
                else:
                    loop.run_until_complete(self.run_cleanup())
            except (RuntimeError, Exception) as e:
                logger.error(f"Error during shutdown: {e}")
                exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered (SIGINT, SIGTERM)")

    async def aenter_context(self, cm):
        """Enter an async context manager and register for cleanup."""
        return await self._exit_stack.enter_async_context(cm)
    
    def register_async_resource(self, coro):
        """Register an async resource cleanup."""
        self._exit_stack.push_async_callback(coro)

shutdown_manager = ShutdownManager()

async def get_shutdown_manager() -> ShutdownManager:
    return shutdown_manager