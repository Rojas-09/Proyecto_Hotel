import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

storage_url = os.environ.get("RATELIMIT_STORAGE_URL")
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri=storage_url)
