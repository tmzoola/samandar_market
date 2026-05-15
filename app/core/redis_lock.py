"""
Redis-based distributed lock for scheduler tasks.
This ensures only one instance executes scheduled tasks in a multi-instance deployment.
"""

import logging
import uuid
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class RedisDistributedLock:
    """
    Distributed lock using Redis to ensure only one instance runs scheduled tasks.

    Uses Redis SET with NX (only if not exists) and EX (expiration) options
    to implement a robust distributed lock pattern.
    """

    def __init__(self, redis_client, lock_name: str, timeout: int = 300):
        """
        Initialize the distributed lock.

        Args:
            redis_client: Redis client instance (must support async operations)
            lock_name: Unique name for the lock (will be prefixed with 'scheduler:lock:')
            timeout: Lock timeout in seconds (default 5 minutes)
        """
        self.redis_client = redis_client
        self.lock_name = f"scheduler:lock:{lock_name}"
        self.timeout = timeout
        self.lock_value: Optional[str] = None

    async def acquire(self) -> bool:
        """
        Try to acquire the lock.

        Returns:
            True if lock acquired successfully, False if lock is already held
        """
        self.lock_value = str(uuid.uuid4())

        try:
            # SET with NX (only if not exists) and EX (expiration)
            # This is an atomic operation in Redis
            result = await self.redis_client.set(
                self.lock_name,
                self.lock_value,
                nx=True,  # Only set if key doesn't exist
                ex=self.timeout,  # Expire after timeout seconds
            )

            if result:
                logger.debug(f"🔒 Lock acquired: {self.lock_name}")
                return True
            else:
                logger.debug(f"⏭️  Lock already held: {self.lock_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error acquiring lock {self.lock_name}: {e}")
            return False

    async def release(self):
        """
        Release the lock if we own it.

        Uses Lua script to ensure we only delete the lock if we own it,
        preventing race conditions.
        """
        if not self.lock_value:
            return

        try:
            # Lua script to safely delete only if we own the lock
            # This prevents accidentally releasing another instance's lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await self.redis_client.eval(
                lua_script, 1, self.lock_name, self.lock_value  # Number of keys
            )

            if result:
                logger.debug(f"🔓 Lock released: {self.lock_name}")
            else:
                logger.debug(
                    f"⚠️  Lock not owned or already released: {self.lock_name}"
                )

        except Exception as e:
            logger.error(f"❌ Error releasing lock {self.lock_name}: {e}")

    async def extend(self, additional_time: int = 60) -> bool:
        """
        Extend the lock timeout if we own it.

        Useful for long-running tasks that need more time than the initial timeout.

        Args:
            additional_time: Additional seconds to add to the lock expiration

        Returns:
            True if lock was extended, False otherwise
        """
        if not self.lock_value:
            return False

        try:
            # Lua script to extend expiration only if we own the lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = await self.redis_client.eval(
                lua_script, 1, self.lock_name, self.lock_value, additional_time
            )

            if result:
                logger.debug(f"⏰ Lock extended: {self.lock_name} (+{additional_time}s)")
                return True
            else:
                logger.debug(f"⚠️  Failed to extend lock: {self.lock_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error extending lock {self.lock_name}: {e}")
            return False

    async def __aenter__(self):
        """Context manager entry - acquire lock."""
        acquired = await self.acquire()
        if not acquired:
            return None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release lock."""
        await self.release()


async def with_redis_lock(
    func: Callable,
    redis_client,
    lock_name: str,
    timeout: int = 300,
    skip_if_locked: bool = True,
):
    """
    Execute a task with Redis distributed lock.

    This wrapper ensures only one instance executes the task at a time.
    Other instances will skip execution if the lock is held.

    Args:
        func: The async function to execute
        redis_client: Redis client instance
        lock_name: Unique name for the lock
        timeout: Lock timeout in seconds (default 5 minutes)
        skip_if_locked: If True, skip execution when lock is held.
                       If False, wait for lock (not recommended for scheduled tasks)

    Example:
        ```python
        async def my_task():
            print("Executing task")

        await with_redis_lock(
            my_task,
            redis_client,
            lock_name="my_scheduled_task",
            timeout=300
        )
        ```
    """
    lock = RedisDistributedLock(redis_client, lock_name, timeout)

    try:
        if await lock.acquire():
            start_time = datetime.now()
            logger.info(f"🔒 Executing task: {lock_name}")

            try:
                # Execute the task
                await func()

                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Task completed: {lock_name} (took {duration:.2f}s)")

            except Exception as e:
                logger.error(f"❌ Task failed: {lock_name} - {e}", exc_info=True)
                raise

            finally:
                # Always release the lock
                await lock.release()
        else:
            if skip_if_locked:
                logger.info(
                    f"⏭️  Task skipped (lock held by another instance): {lock_name}"
                )
            else:
                logger.warning(f"⏸️  Task waiting (lock held): {lock_name}")

    except Exception as e:
        logger.error(f"❌ Error in with_redis_lock for {lock_name}: {e}")
        # Ensure lock is released even on error
        await lock.release()


async def check_lock_status(redis_client, lock_name: str) -> dict:
    """
    Check the status of a lock.

    Args:
        redis_client: Redis client instance
        lock_name: Name of the lock to check

    Returns:
        Dictionary with lock status information
    """
    full_lock_name = f"scheduler:lock:{lock_name}"

    try:
        # Check if lock exists
        exists = await redis_client.exists(full_lock_name)

        if not exists:
            return {"lock_name": lock_name, "locked": False, "owner": None, "ttl": None}

        # Get lock owner and TTL
        owner = await redis_client.get(full_lock_name)
        ttl = await redis_client.ttl(full_lock_name)

        return {"lock_name": lock_name, "locked": True, "owner": owner, "ttl": ttl}

    except Exception as e:
        logger.error(f"Error checking lock status for {lock_name}: {e}")
        return {"lock_name": lock_name, "error": str(e)}


async def force_release_lock(redis_client, lock_name: str) -> bool:
    """
    Force release a lock (use with caution).

    This should only be used in emergency situations or for cleanup.

    Args:
        redis_client: Redis client instance
        lock_name: Name of the lock to release

    Returns:
        True if lock was deleted, False otherwise
    """
    full_lock_name = f"scheduler:lock:{lock_name}"

    try:
        result = await redis_client.delete(full_lock_name)
        if result:
            logger.warning(f"🔓 Force released lock: {lock_name}")
            return True
        else:
            logger.info(f"Lock not found: {lock_name}")
            return False

    except Exception as e:
        logger.error(f"Error force releasing lock {lock_name}: {e}")
        return False
