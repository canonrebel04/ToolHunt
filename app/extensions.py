"""Flask application extensions (cache, db, etc.)."""

from flask_caching import Cache
from flask_cors import CORS

cache = Cache()
cors = CORS()
