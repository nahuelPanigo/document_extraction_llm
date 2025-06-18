import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

