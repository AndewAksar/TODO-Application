import logging
from operator import countOf

from services.shared.logging import configure_logging

def test_logging_bootstrap_does_not_crash():
    configure_logging(service_name="test-service")

    logger = logging.getLogger("smoke")
    logger.info("Hello, world!")
