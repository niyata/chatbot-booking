import os
from os import path
from config import TIMEZONE, SPREADSHEETID
from datetime import datetime, timedelta
import time
from pytz import timezone
import json
import calendar
import models

pj = path.join

CLIENTS_CACHE_VALID = 'CLIENTS_CACHE_VALID'

def p(pt):
    return pj(path.dirname(__file__), pt)

def listGet(ls, index, default = None):
    try:
        return ls[index]
    except IndexError:
        return default
        
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def local2utc(dt):
    utc_st = dt.replace(tzinfo=timezone(TIMEZONE)).astimezone(timezone('UTC'))
    return utc_st
def utc2local(dt, tz = TIMEZONE):
    return  dt.replace(tzinfo=timezone('UTC')).astimezone(timezone(tz))
def getWeekDays(dt):
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone(TIMEZONE))
    else:
        dt = dt.astimezone(timezone(TIMEZONE))
    # weekday of Monday is 0
    monday = dt - timedelta(days=dt.weekday())
    weekdays = [monday]
    for i in range(1, 7):
        weekdays.append(monday + timedelta(days=i))
    return weekdays

def addMonths(dt,months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day,calendar.monthrange(year,month)[1])
    return dt.replace(year=year, month = month,day=day)

def toTimestamp(dt):
    return int(time.mktime(dt.timetuple()))
def toDatetime(ts):
    return datetime.fromtimestamp(ts)
gcService = None
def getGoogleCalendarService():
    global gcService
    if not gcService:
        import httplib2
        from apiclient import discovery
        from get_google_calendar_credentials import get_google_calendar_credentials
        credentials = get_google_calendar_credentials()
        http = credentials.authorize(httplib2.Http())
        gcService = discovery.build('calendar', 'v3', http=http)
    return gcService

gsService = None
def getGoogleSheetService():
    global gsService
    if not gsService:
        import httplib2
        from apiclient import discovery
        from get_google_sheet_credentials import get_google_sheet_credentials
        credentials = get_google_sheet_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
        gsService = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)
    return gsService

def updateSheet(body, rangeName = 'Sheet1', valueInputOption='USER_ENTERED'):
    spreadsheetId = SPREADSHEETID
    service = getGoogleSheetService()
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheetId, range=rangeName,
        valueInputOption=valueInputOption, body=body).execute()
    setting({CLIENTS_CACHE_VALID: False})
    print('{0} cells updated.'.format(result.get('updatedCells')))
    return result
# create google calendar event
def createEvent(name, time, lastHours=1):
    service = getGoogleCalendarService()
    endTime = time + timedelta(hours=lastHours)
    event = {
      'summary': name,
      # 'location': '800 Howard St., San Francisco, CA 94103',
      # 'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        # 'dateTime': '2015-05-28T09:00:00-07:00',
        'dateTime': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'timeZone': TIMEZONE,
      },
      'end': {
        'dateTime': endTime.strftime('%Y-%m-%dT%H:%M:%S'),
        'timeZone': TIMEZONE,
      },
      # 'recurrence': [
      #   'RRULE:FREQ=DAILY;COUNT=2'
      # ],
      # 'attendees': [
      #   {'email': 'lpage@example.com'},
      #   {'email': 'sbrin@example.com'},
      # ],
      # 'reminders': {
      #   'useDefault': False,
      #   'overrides': [
      #     {'method': 'email', 'minutes': 24 * 60},
      #     {'method': 'popup', 'minutes': 10},
      #   ],
      # },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    return event

def sendSms(phone, msg):
    from twilio.rest import Client
    from config import SPREADSHEETID, sms_account_sid, sms_auth_token, sms_from
    client = Client(sms_account_sid, sms_auth_token)
    client.api.account.messages.create(
        to=phone,
        from_=sms_from,
        body=msg)

def getSheetValues(rangeName = 'Sheet1'):
    service = getGoogleSheetService()
    spreadsheetId = SPREADSHEETID
    rangeName = 'Sheet1'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    sheetRows = result.get('values', [])
    return sheetRows
def getClientFilter():
    if not setting(CLIENTS_CACHE_VALID):
        from cassandra.cqlengine import connection
        from cassandra.cqlengine.query import BatchQuery
        session = connection.get_connection().session
        session.execute('TRUNCATE client;')
        values = getSheetValues()
        with BatchQuery() as b:
            for i, row in enumerate(values):
                # 0 is head
                if i  ==  0:
                    continue
                lineNumber = i + 1
                row2 = [listGet(row, j, '').strip() for j in range(4)]
                notEmpty = False
                for j in row2:
                    if row2[j]:
                        notEmpty = True
                        break
                if notEmpty:
                    models.client.batch(b).create(id=lineNumber, phone=row2[0], name=row2[1], full_name=row2[2], facebook_id=row2[3])
    return models.client.objects()
def getGoogleStrTime(dt):
    return dt.replace(tzinfo=None).isoformat() + 'Z' # 'Z' indicates UTC time
def getEventsByPhone(phone):
    service = getGoogleCalendarService()
    today = utc2local(datetime.utcnow())
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today = local2utc(today)
    today = getGoogleStrTime(today)
    eventsResult = service.events().list(
        calendarId='primary', singleEvents=True, q =phone, timeMin=today,
        orderBy='startTime').execute()
    events = eventsResult.get('items')
    if not events:
        return None
    events.reverse()
    return events
def getEventById(evid):
    service = getGoogleCalendarService()
    return service.events().get(calendarId='primary', eventId=evid).execute()
def getBookingDateFromEvent(event, fmt = '%Y-%m-%d %H:%M'):
    start = datetime.strptime(event['start']['dateTime'][:19], "%Y-%m-%dT%H:%M:%S")
    bookingDatetime = start.strftime(fmt)
    return bookingDatetime
def userCacheGet(id, name, default=None):
    user = models.user.objects.filter(id=id).first()
    cache = {} if not user else json.loads(user.cache)
    return cache.get(name, default)
def userCacheSet(id, name, value):
    user = models.user.objects.filter(id=id).first()
    if not user:
        models.user.create(id=id, cache=json.dumps({}))
    user = models.user.objects.filter(id=id).first()
    cache = json.loads(user.cache)
    if value == None:
        if name in cache:
            del cache[name]
    else:
        cache[name] = value
    user.cache = json.dumps(cache)
    user.save()
def setting(name, default=None):
    item = models.key_value.objects.filter(key='setting').first()
    dc = {} if not item else json.loads(item.value)
    if isinstance(name, dict):
        # set
        toset = name
        for k, v in toset.items():
            dc[k] = v
        dcStr = json.dumps(dc)
        if not item:
            item = models.key_value(key='setting')
        item.value = dcStr
        item.save()
    else:
        # get
        return dc.get(name, default)
# deprecated
phoneEventFp = p('phone-event.json')
def addPhoneEventMapping(phone, eventId):
    fp = phoneEventFp
    if not os.path.exists(fp):
        with open(fp, 'w') as target:
            target.write('{}')
    mapping = None
    with open(fp) as f:
        mapping = json.loads(f.read())
        if phone not in mapping:
            mapping[phone] = []
        mapping[phone].append(eventId)
    with open(fp, 'w') as target:
        target.write(json.dumps(mapping))

def getEventIdByPhone(phone):
    fp = phoneEventFp
    if not os.path.exists(fp):
        return None
    with open(fp) as f:
        mapping = json.loads(f.read())
        return mapping.get(phone)

def getLogger(fp):
    import logging
    from logging.handlers import TimedRotatingFileHandler
    # logger
    LOG_FILE = fp
    #logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',datefmt='%Y-%m-%d %I:%M:%S',filemode='w')   #for term print
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    # one log file per day, keep 30 files at most; 日志文件(天), 最多30个
    fh = TimedRotatingFileHandler(LOG_FILE,when='D',interval=1,backupCount=30)
    datefmt = '%Y-%m-%d %H:%M:%S'
    format_str = '%(asctime)s %(levelname)s %(message)s '
    #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    formatter = logging.Formatter(format_str, datefmt)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger