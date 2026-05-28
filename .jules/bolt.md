## 2024-05-27 - Response Compression Middleware
**Learning:** Adding response compression middleware (Flask-Compress) drastically improved data transfer efficiency for large JSON payloads, but required careful testing configuration (payload > 500 bytes and valid `Accept-Encoding: gzip` headers). Also, the SQLite WAL mode is critical for handling concurrency on the lazy-loaded index without locking the thread map.
**Action:** Always enable response compression with an appropriate `COMPRESS_MIN_SIZE` for large textual responses, and be sure to mock large payloads in tests.
