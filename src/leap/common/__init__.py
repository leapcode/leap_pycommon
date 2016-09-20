import logging

from leap.common import certs
from leap.common import check
from leap.common import files
from leap.common import events
from ._version import get_versions

logger = logging.getLogger(__name__)

try:
    import pygeoip
    HAS_GEOIP = True
except ImportError:
    # logger.debug('PyGeoIP not found. Disabled Geo support.')
    HAS_GEOIP = False

__all__ = ["certs", "check", "files", "events"]

__version__ = get_versions()['version']
del get_versions
