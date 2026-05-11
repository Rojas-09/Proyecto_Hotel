from datetime import datetime, timezone, timedelta

COLOMBIA_TZ = timezone(timedelta(hours=-5))


def ahora_colombia():
    return datetime.now(COLOMBIA_TZ)