from utils import getGoogleSheetService, getGoogleCalendarService, sendSms
from utils import getSheetValues,findRow, getBookingDateFromEvent, listGet, getGoogleStrTime
from datetime import datetime, timedelta
from config import SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, schedule_delay
import time
import urllib.parse
from fbmq import Page, Template

# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)


while True:
    print('Getting the upcoming events')
    service = getGoogleCalendarService()
    now = datetime.utcnow()
    endTime = now + timedelta(hours=1)
    now = getGoogleStrTime(now)
    endTime = getGoogleStrTime(endTime)
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

    for event in events:
        ls = event['summary'].split(' ')
        phone = ls[0]
        name = ls[1]
        row = findRow(sheetRows, phone)
        if not row:
            print('row not found for event: %s'%(event['summary']))
            continue
        print(row)
        phone = row[0]
        facebookid = listGet(row, 3)
        bookingDatetime = getBookingDateFromEvent(event)
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
            page.send(facebookid, msgFront)
            print('fb message sent', msgFront)
    time.sleep(schedule_delay)
