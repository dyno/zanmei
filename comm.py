import os

from absl import flags, logging as log

TOTAL = 527

FLAGS = flags.FLAGS


async def fetch(session, url):
    log.info(f"fetching {url}")
    async with session.get(url) as response:
        status = response.status
        content = await response.content.read()
        return status, content


def init_logging():
    logdir = "logs"
    os.makedirs(logdir, exist_ok=True)
    handler = log.get_absl_handler()
    handler.use_absl_log_file(log_dir=logdir)
    if not FLAGS["alsologtostderr"].present:
        FLAGS["alsologtostderr"].value = True


def zip_blank_lines(lines):
    blank = False
    for line in lines:
        if line:
            blank = False
            yield line
        else:
            if blank:
                continue
            yield line
            blank = True
