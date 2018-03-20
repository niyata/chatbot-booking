import os
from os import path
from config import TIMEZONE
from datetime import datetime, timedelta
import time
from pytz import timezone

pj = path.join

def p(pt):
    return pj(path.dirname(__file__), pt)


def local2utc(dt):
    utc_st = dt.replace(tzinfo=timezone(TIMEZONE)).astimezone(timezone('UTC'))
    return utc_st

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

# create google calendar event
def createEvent(name, time, lastHours):
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

def sendSms(phone, msg):
    from twilio.rest import Client
    from config import SPREADSHEETID, sms_account_sid, sms_auth_token, sms_from
    client = Client(sms_account_sid, sms_auth_token)
    client.api.account.messages.create(
        to=phone,
        from_=sms_from,
        body=msg)
