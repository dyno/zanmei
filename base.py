import logging
from pathlib import Path
from typing import Optional

from absl import flags, logging as log

FLAGS = flags.FLAGS
CWD_LOG_DIR = "logs"


def initialize_logging(log_dir: Optional[str] = None) -> None:
    """Initialize logging system"""
    # log_dir is a gflag defined in absl.logging
    if log_dir is None:
        log_dir = FLAGS["log_dir"].value
    if not log_dir:
        log_dir = CWD_LOG_DIR
    FLAGS["log_dir"].value = log_dir

    # mkdir -p ${log_dir}
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    handler = log.get_absl_handler()
    handler.use_absl_log_file(log_dir=log_dir)
    log.use_absl_handler()

    # set alsologtostderr as default behavior.
    if not FLAGS["alsologtostderr"].present:
        FLAGS["alsologtostderr"].value = True

    # default verbosity to INFO
    if not FLAGS["verbosity"].present:
        FLAGS["verbosity"].value = 0
        logging.root.setLevel(logging.INFO)
