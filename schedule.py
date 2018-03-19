from utils import getGoogleSheetService, getGoogleCalendarService, sendSms
from datetime import datetime, timedelta
from config import SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, schedule_delay
import requests
import time
import urllib.parse

service = getGoogleCalendarService()

while True:
    print('Getting the upcoming events')
    now = datetime.datetime.utcnow()
    endTime = time + timedelta(hours=1)
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
    def findRow(phone, name):
        return next(row for row in sheetRows if row[0] == phone and row[1] == name)

    for event in events:
        ls = event['summary'].split(' ')
        phone = ls[0]
        name = ls[1]
        row = findRow(phone, name)
        facebookid = row[3]
        if facebookid:
            # send fb msg
            msgDict = {
                "messaging_type": "RESPONSE",
                "recipient": {
                    "id": facebookid
                },
                "message": {
                    "text": "todo"
                }
            }
            r = requests.post('https://graph.facebook.com/v2.6/me/messages?access_token=%s'%(fb_PAGE_ACCESS_TOKEN), data=msgDict)
            print(r.text)
        else:
            # send sms
            msg = 'Booking date: %s https://www.messenger.com/t/498812477183171?phone=%s'%(row[4], urllib.parse.urlencode({'phone': row[0]}))
            sendSms(phone, msg)
    time.sleep(schedule_delay)
