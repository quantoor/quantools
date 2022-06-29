import datetime as dt


def date_to_timestamp_sec(year, month, day, hour):
    date = dt.datetime(year, month, day, hour)
    return int(dt.datetime.timestamp(date))


def timestamp_now():
    return int(dt.datetime.now().timestamp())

# endDate = datetime.today()
# startDate = endDate - timedelta(days=7)
# startTsMs = int(datetime.timestamp(startDate) * 1000)
