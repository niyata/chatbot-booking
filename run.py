import init
import logging
from flask import Flask, request
import config
from config import app_host, app_port
from config import TIMEZONE, SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, fb_VERIFY_TOKEN
from utils import createEvent, getGoogleSheetService, getEventsByPhone, getBookingDateFromEvent
from utils import getSheetValues,findRow, findRowByFbid, getEventById, chunks, getGoogleCalendarService
from utils import getWeekDays, toTimestamp, toDatetime, getSheetData, updateSheet, utc2local, addMonths
from utils import listGet, p, userCacheGet, userCacheSet
from datetime import datetime, timedelta
import time
from fbmq import Page, Template
import re
from googleapiclient.errors import HttpError
from lang import trans, strfweekday
import json


# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)

# constant
VIEW_MY_BOOKING = 'VIEW_MY_BOOKING'
CANCEL_MY_BOOKING = 'CANCEL_MY_BOOKING'
CONFIRM_CANCEL_MY_BOOKING = 'CONFIRM_CANCEL_MY_BOOKING'
MAKE_A_BOOKING = 'MAKE_A_BOOKING'
CHOOSE_A_WEEK = 'CHOOSE_A_WEEK'
CHOOSE_A_DAY = 'CHOOSE_A_DAY'
CHOOSE_LANGUAGE = 'CHOOSE_LANGUAGE'

# init app
app = Flask(__name__)

def sendMsg(sender_id, name):
    return page.send(sender_id, trans(sender_id, name))

# actions
@app.route("/")
def hello():
    return "Hello World!"


@app.route("/create-events")
def createEvents():
    rows = getSheetData()
    if rows:
        events = []
        for i, row in enumerate(rows[1:]):
            # Print columns A and E, which correspond to indices 0 and 4.
            # print('%s, %s' % (row[0], row[4]))
            if len(row) > 7 and row[4] and row[5] and row[6] and row[7]:
                if '/' in row[4]:
                    m, d, y = row[4].split('/')
                else:
                    y, m, d = row[4].split('-')
                y = int(y)
                m = int(m)
                d = int(d)
                time = datetime.now()
                time = time.replace(month=m, day=d, year=y, hour=int(
                    row[5]), minute=int(row[6]), second=0)
                events.append(['%s %s (%s)' %
                               (row[0], row[1], row[2]), time, float(row[7]), i])
                row[4] = ''
                row[5] = ''
                row[6] = ''
                row[7] = ''
        #
        for value in events:
            createEvent(*value[:-1])

        # save cleared
        if len(events) > 0:
            body = {
                'values': rows
            }
            updateSheet(body)
    return 'ok'

# facebook


@app.route('/webhook', methods=['GET'])
def validate():
    if request.args.get('hub.mode', '') == 'subscribe' and \
            request.args.get('hub.verify_token', '') == fb_VERIFY_TOKEN:

        print("Validating webhook")

        return request.args.get('hub.challenge', '')
    else:
        return 'Failed validation. Make sure the validation tokens match.'


@app.route('/webhook', methods=['POST'])
def webhook():
    requestStr = request.get_data().decode('utf-8')
    # e.g.: {"object":"page","entry":[{"id":"498812477183171","time":1522222835374,"messaging":[{"recipient":{"id":"498812477183171"},"timestamp":1522222835374,"sender":{"id":"1286804074753753"},"postback":{"payload":"CHOOSE_A_DAY_1522566413","title":"Sun (04-01)"}}]}]}
    # ignore encode error when facebook request data including utf8 chars
    try:
        page.handle_webhook(requestStr)
    except UnicodeEncodeError as e:
        pass
    except:
        sender_id = json.loads(requestStr).get('entry')[0]['messaging'][0]['sender']['id']
        sendMsg(sender_id, 'sys_error')
        logging.exception("Uncaught error in webhook")
    return "ok"


def sendButtons(to_id, title, buttons):
    title = trans(to_id, title)
    for chunked in chunks(buttons, 3):
        for btn in chunked:
            btn['title'] = trans(to_id, btn['title'])
        page.send(to_id, Template.Buttons(title, chunked))

def start(event):
    sender_id = event.sender_id
    locale = userCacheGet(sender_id, 'locale')
    if not locale:
        sendLanguagePicker(sender_id)
    else:
        buttons = [
            {
                "type": "postback",
                "value": VIEW_MY_BOOKING,
                "title": 'view_booking',
            },
            {
                "type": "postback",
                "value": CANCEL_MY_BOOKING,
                "title": 'cancel_booking',
            },
            {
                "type": "postback",
                "value": MAKE_A_BOOKING,
                "title": 'make_booking',
            },
        ]
        sendButtons(sender_id, 'hello', buttons)
def sendLanguagePicker(sender_id):
    buttons = [
            {
                "type": "postback",
                "value": CHOOSE_LANGUAGE + '_en',
                "title": "English"
            },
            {
                "type": "postback",
                "value": CHOOSE_LANGUAGE + '_zh',
                "title": "中文"
            },
        ]
    sendButtons(sender_id, 'pls_choose_language', buttons)
@page.callback([CHOOSE_LANGUAGE + '_(.+)'])
def choose_language(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    locale = payload[len(CHOOSE_LANGUAGE) + 1:]
    userCacheSet(sender_id, 'locale', locale)
    start(event)

@page.handle_message
def message_handler(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    message = event.message_text
    print('receive msg', sender_id)
    if re.match(r'^\d\d?-\d\d?$', message):
        # date
        m,d = message.split('-')
        m = int(m)
        d = int(d)
        dt = utc2local(datetime.utcnow())
        try:
            dt = addMonths(dt, 1)
        except Exception as e:
            sendMsg(sender_id, 'invalid_date')
            return
        if dt.month != m:
            sendMsg(sender_id, 'date_not_next_month')
            return
        try:
            dt = dt.replace(day=d)
        except:
            sendMsg(sender_id, 'invalid_input')
            return
        setDate(dt, event)
    elif re.match(r'^\d\d?:\d\d?$', message):
        # time
        h,m = message.split(':')
        setTime([int(h), int(m)], event)
    else:
        t = message.lower()
        if 'language' in t or 'locale' in t or '语言' in t:
            sendLanguagePicker(sender_id)
        else:
            start(event)

@page.handle_referral
def handler2(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    # page.send(sender_id, "thank you! your message is '%s'" % message)
    try:
        phone = event.referral['ref']
    except Exception as e:
        phone = None
    if phone:
        print('phone', phone)
        sheetRows = getSheetData()
        row = findRow(sheetRows, phone)
        if row:
            if listGet(row, 3, '').strip():
                print('record already has facebook id.')
            else:
                print('store facebook id in google sheet')
                values = [
                    [
                        sender_id
                    ],
                    # Additional rows ...
                ]
                body = {
                    'values': values
                }
                rowIndex = sheetRows.index(row)
                # sheet row index start from 1
                rangeName = 'Sheet1!D%s:D%s' % (rowIndex+1, rowIndex+1)
                updateSheet(body, rangeName)
                print('facebook id stored in google sheet')
        else:
            print('no record found with given phone')
    print('no ref(phone) in hook event')
    start(event)

@page.callback([VIEW_MY_BOOKING])
def callback_1(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        events = getEventsByPhone(row[0])
        if not events:
            sendMsg(sender_id, 'no_record')
            print('no booking record found', sender_id)
        else:
            bkdt = trans(sender_id, 'booking_date')
            ls = ['%s: %s'%(bkdt, getBookingDateFromEvent(event)) for event in events]
            page.send(sender_id, '\n'.join(ls))
    else:
        sendMsg(sender_id, 'no_record')

@page.callback([CANCEL_MY_BOOKING])
def callback_2(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        events = getEventsByPhone(row[0])
        if not events:
            sendMsg(sender_id, 'no_record')
            print('no booking record found', sender_id)
        else:
            if len(events) == 1:
                bookingDatetime = getBookingDateFromEvent(events[0])
                bkdt = trans(sender_id, 'booking_date')
                bookingInfo = '%s: %s'%(bkdt, bookingDatetime)
                buttons = [
                    {
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": 'confirm_cancel'

                    },
                ]
                sendButtons(sender_id, bookingInfo, buttons)
            else:
                buttons = []
                for event in events:
                    bookingDatetime = getBookingDateFromEvent(event, '%m-%d %H:%M')
                    bookingInfo = trans(sender_id, 'booking') + ': ' + bookingDatetime
                    buttons.append({
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": bookingInfo,
                    })

                sendButtons(sender_id, 'choose_cancel', buttons)
    else:
        sendMsg(sender_id, 'no_record')
        print('no booking record found', sender_id)

@page.callback([CONFIRM_CANCEL_MY_BOOKING + '_(.+)'])
def callback_3(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    evid = payload[len(CONFIRM_CANCEL_MY_BOOKING) + 1:]
    event = getEventById(evid)
    if not event:
        sendMsg(sender_id, 'no_record')
        print('no booking record found', sender_id)
    else:
        bookingDatetime = getBookingDateFromEvent(event)
        service = getGoogleCalendarService()
        try:
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
        except HttpError as e:
            if e.resp.status in [410]:
                # already deleted
                pass
            else:
                raise e
        time.sleep(1)
        event = getEventById(evid)
        if event:
            sendMsg(sender_id, 'failed_cancel')
            print('Failed to cancel the booking', sender_id, event)
        else:
            page.send(sender_id, trans(sender_id, 'cancelled_successfully')%(bookingDatetime))
            print('Booking canceled successfully', sender_id, event)

@page.callback([MAKE_A_BOOKING])
def callback_4(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    buttons = []
    titles = ['this_week', 'next_week', 'week_after_next', 'week_after_next2', 'next_month']
    for i in range(5):
        buttons.append({
            "type": "postback",
            "value": CHOOSE_A_WEEK + '_' + str(i),
            "title": titles[i]
        })
    sendButtons(sender_id, 'pls_choose', buttons)

@page.callback([CHOOSE_A_WEEK + r'_(\d)'])
def callback_5(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    n = int(payload[len(CHOOSE_A_WEEK) + 1:])
    if n < 4:
        # week
        t = datetime.utcnow() + timedelta(weeks=n)
        weekdays = getWeekDays(t)
        buttons = [{"type": "postback", "value": CHOOSE_A_DAY + '_' + str(toTimestamp(v)), "title": strfweekday(sender_id, v, '%a (%m-%d)')} for v in weekdays]
        sendButtons(sender_id, 'pls_choose', buttons)
    else:
        # next month
        sendMsg(sender_id, 'pls_input_date')
@page.callback([CHOOSE_A_DAY + r'_(\d+)'])
def callback_6(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    n = int(payload[len(CHOOSE_A_DAY) + 1:])
    dt = toDatetime(n)
    return setDate(dt, event)

def setDate(dt, event):
    sender_id = event.sender_id
    print('set date', sender_id)
    userCacheSet(sender_id, 'date', str(toTimestamp(dt)))
    sendMsg(sender_id, 'pls_input_time')

def setTime(timeList, event):
    sender_id = event.sender_id
    print('set time', sender_id)
    t = userCacheGet(sender_id, 'date')
    if not t:
        sendMsg(sender_id, 'pls_set_date_before_time')
        return
    dt = toDatetime(int(t))
    h, m = timeList
    try:
        dt = dt.replace(hour=h, minute=m, second=0, microsecond=0)
    except:
        sendMsg(sender_id, 'invalid_input')
        return
    rows = getSheetData()
    if rows:
        row = findRowByFbid(rows,sender_id)
        if not row:
            sendMsg(sender_id, 'no_record')
            return
        createEvent('%s %s (%s)' %(row[0], row[1], row[2]), dt)
        sendMsg(sender_id, 'booked_successfully')


@page.after_send
def after_send(payload, response):
    """:type payload: fbmq.Payload"""
    print("complete")

# bootstrap app
if __name__ == '__main__':
    app.run(host=app_host, port=app_port, debug=True, threaded=True)
