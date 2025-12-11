from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack

from aiobotocore.client import AioBaseClient
from aiobotocore.session import AioSession
from botocore.client import Config
from environs import env
env.read_env()


params = {
    "service_name": "s3",
    "aws_access_key_id": env("KEY_ID"),
    "aws_secret_access_key": env("KEY_SECRET"),
    "region_name": env("REGION"),
    "endpoint_url": env("ENDPOINT"),
    "config": Config(s3={"addressing_style": "virtual"})
}


async def create_async_client(session: AioSession, exit_stack: AsyncExitStack):
    context_manager = session.create_client(**params)
    client = await exit_stack.enter_async_context(context_manager)
    return client


async def get_async_client() -> AsyncGenerator[AioBaseClient, None]:
    session = AioSession()
    async with AsyncExitStack() as exit_stack:
        client = await create_async_client(session, exit_stack)
        yield client
