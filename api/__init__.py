import os
import json
from flask import Flask
from redis import Redis
from api.years import years
from api.views import views
from api.segments import segments
from api.job_types import job_types
from api.redis_session import RedisSessionInterface

try:
    from raven.contrib.flask import Sentry
    from api.app_config import SENTRY_DSN
    sentry = Sentry(dsn=SENTRY_DSN)
except ImportError:
    sentry = None
except KeyError:
    sentry = None

def create_app():
    app = Flask(__name__)
    app.config.from_object('api.app_config')
    redis = Redis()
    app.session_interface = RedisSessionInterface(redis=redis)
    if sentry:
        sentry.init_app(app)
    app.register_blueprint(years)
    app.register_blueprint(views)
    app.register_blueprint(segments)
    app.register_blueprint(job_types)
    return app

