"""Flask application extensions (cache, db, etc.)."""

from flask_caching import Cache
from flask_compress import Compress

cache = Cache()
compress = Compress()
