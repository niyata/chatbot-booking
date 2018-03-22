from utils import getGoogleSheetService, getGoogleCalendarService, sendSms
from datetime import datetime, timedelta
from config import SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, schedule_delay
import requests
import time
import urllib.parse


while True:
    print('Getting the upcoming events')
    service = getGoogleCalendarService()
    now = datetime.utcnow()
    endTime = now + timedelta(hours=1)
    now = now.isoformat() + 'Z' # 'Z' indicates UTC time
    endTime = endTime.isoformat() + 'Z' # 'Z' indicates UTC time
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, timeMax= endTime, maxResults=2500, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')

    # get sheet
    spreadsheetId = SPREADSHEETID
    rangeName = 'Sheet1'
    service = getGoogleSheetService()
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    sheetRows = result.get('values', [])
    def findRow(phone):
        try:
            return next(row for row in sheetRows if row[0] == phone)
        except StopIteration as e:
            return None

    for event in events:
        ls = event['summary'].split(' ')
        phone = ls[0]
        name = ls[1]
        row = findRow(phone)
        if not row:
            print('row not found for event: %s'%(event['summary']))
            continue
        print(row)
        phone = row[0]
        facebookid = row[3]
        start = datetime.strptime(event['start']['dateTime'][:19], "%Y-%m-%dT%H:%M:%S")
        bookingDatetime = start.strftime('%Y-%m-%dT%H:%M:%S')
        msgFront = 'Hi %s, Your booking is %s.'%(row[1], bookingDatetime)
        if phone:
            # send sms
            # link = 'https://www.messenger.com/t/498812477183171?%s'%(urllib.parse.urlencode(params))
            link = 'http://m.me/498812477183171?ref='+(phone if not facebookid else '')
            msg = msgFront + ' For more info pleaes check out our chatbot %s.'%(link)
            sendSms(phone, msg)
            print('sms sent', msg)
        if facebookid:
            # send fb msg
            msgDict = {
                "messaging_type": "RESPONSE",
                "recipient": {
                    "id": facebookid
                },
                "message": {
                    "text": msgFront,
                }
            }
            r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s'%(fb_PAGE_ACCESS_TOKEN), json=msgDict)
            print('fb message sent', r.text)
    time.sleep(schedule_delay)
