from typing import Tuple

from absl import flags, logging as log
from aiohttp import ClientSession

FLAGS = flags.FLAGS


async def fetch(session: ClientSession, url: str) -> Tuple[int, str]:
    log.info(f"fetching {url}")
    async with session.get(url) as response:
        status = response.status
        content = await response.content.read()
        return status, content


def zip_blank_lines(lines):
    """If there are multiple blank lines, generate only one."""
    first_blank_line = False
    for line in lines:
        if line:
            first_blank_line = False
            yield line
        else:
            if first_blank_line:
                continue
            yield line
            first_blank_line = True
