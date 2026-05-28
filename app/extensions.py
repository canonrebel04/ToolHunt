"""Flask application extensions (cache, db, etc.)."""

from flask_caching import Cache

cache = Cache()
from flask_compress import Compress

compress = Compress()
