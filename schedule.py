import init
import logging
from utils import getGoogleSheetService, getGoogleCalendarService, sendSms
from utils import getSheetValues, getClientFilter, getBookingDateFromEvent, listGet, getGoogleStrTime
from utils import utc2local, p
from datetime import datetime, timedelta
from config import SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, schedule_delay
import time
import urllib.parse
from fbmq import Page, Template
from lang import trans
import config

# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)

while True:
    logging.info('wake up')
    logging.info('Getting the upcoming events')
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
        logging.info('No upcoming events found.')

    for event in events:
        ls = event['summary'].split(' ')
        phone = ls[0]
        name = ls[1]
        row = getClientFilter().filter(phone=phone).first()
        if not row:
            logging.info('row not found for event: %s'%(event['summary']))
            continue
        phone = row.phone
        facebookid = row.facebook_id
        bookingDatetime = getBookingDateFromEvent(event)
        msgFront = trans(facebookid, 'your_booking_is')%(row.name, bookingDatetime)

        if phone:
            # send sms
            # link = 'https://www.messenger.com/t/498812477183171?%s'%(urllib.parse.urlencode(params))
            link = 'http://m.me/498812477183171?ref='+(phone if not facebookid else '')
            msg = msgFront + ' ' + trans(facebookid, 'pls_check_chatbot')%(link)
            sendSms(phone, msg)
            logging.info('sms sent: ' + msg)
        if facebookid:
            # send fb msg
            page.send(facebookid, msgFront)
            logging.info('fb message sent:' + msgFront)
    time.sleep(schedule_delay)
