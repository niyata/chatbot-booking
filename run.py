from flask import Flask, request
from config import TIMEZONE, SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, fb_VERIFY_TOKEN
from utils import createEvent, getGoogleSheetService, getEventsByPhone, getBookingDateFromEvent
from utils import getSheetValues,findRow, findRowByFbid, getEventById, chunks, getGoogleCalendarService
from utils import getWeekDays, toTimestamp, toDatetime, getSheetData, updateSheet, utc2local, addMonths
from utils import listGet
from datetime import datetime, timedelta
import time
from fbmq import Page, Template
import re
from googleapiclient.errors import HttpError
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)

# constant
VIEW_MY_BOOKING = 'VIEW_MY_BOOKING'
CANCEL_MY_BOOKING = 'CANCEL_MY_BOOKING'
CONFIRM_CANCEL_MY_BOOKING = 'CONFIRM_CANCEL_MY_BOOKING'
MAKE_A_BOOKING = 'MAKE_A_BOOKING'
CHOOSE_A_WEEK = 'CHOOSE_A_WEEK'
CHOOSE_A_DAY = 'CHOOSE_A_DAY'

# init app
app = Flask(__name__)

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
    page.handle_webhook(request.get_data(as_text=True))
    return "ok"


def sendButtons(to_id, title, buttons):
    for value in chunks(buttons, 3):
        page.send(to_id, Template.Buttons(title, value))
def sendStartButtons(sender_id):
    buttons = [
        {
            "type": "postback",
            "value": VIEW_MY_BOOKING,
            "title": "View my booking"
        },
        {
            "type": "postback",
            "value": CANCEL_MY_BOOKING,
            "title": "Cancel my booking"
        },
        {
            "type": "postback",
            "value": MAKE_A_BOOKING,
            "title": "Make a booking"
        },
    ]
    sendButtons(sender_id, buttons, 'hello')

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
            page.send(sender_id, str(e))
            return
        if dt.month != m:
            page.send(sender_id, 'Input date is not in next month')
            return
        dt = dt.replace(day=d)
        setDate(dt, event)
    elif re.match(r'^\d\d?:\d\d?$', message):
        # time
        h,m = message.split(':')
        setTime([int(h), int(m)], event)
    else:
        sendStartButtons(sender_id)

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
            if listGet(row, 3):
                print('record already has facebook id')
            else:
                print('store facebook id in google sheet')
                values = [
                    [
                        phone
                    ],
                    # Additional rows ...
                ]
                body = {
                    'values': values
                }
                rowIndex = sheetRows.index(row)
                rangeName = 'Sheet1!D%s:D%s' % (rowIndex, rowIndex)
                updateSheet(body, rangeName)
                print('facebook id stored in google sheet')
        else:
            print('no record found with given phone')
    print('no ref(phone) in hook event')
    sendStartButtons(sender_id)

@page.callback([VIEW_MY_BOOKING])
def callback_1(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        events = getEventsByPhone(row[0])
        if not events:
            page.send(sender_id, 'No booking record found for you')
            print('no booking record found', sender_id)
        else:
            ls = ['Booking date: %s'%(getBookingDateFromEvent(event)) for event in events]
            page.send(sender_id, '\n'.join(ls))
    else:
        page.send(sender_id, 'No booking record found for you')
        print('no booking record found', sender_id)

@page.callback([CANCEL_MY_BOOKING])
def callback_2(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        events = getEventsByPhone(row[0])
        if not events:
            page.send(sender_id, 'No booking record found for you')
            print('no booking record found', sender_id)
        else:
            if len(events) == 1:
                bookingDatetime = getBookingDateFromEvent(events[0])
                bookingInfo = 'Booking date: %s'%(bookingDatetime)
                buttons = [
                    {
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": "Confirm to cancel my booking"
                    },
                ]
                sendButtons(sender_id, bookingInfo, buttons)
            else:
                buttons = []
                for event in events:
                    bookingDatetime = getBookingDateFromEvent(event, '%m-%d %H:%M')
                    bookingInfo = 'Booking: %s'%(bookingDatetime)
                    buttons.append({
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": bookingInfo,
                    })

                sendButtons(sender_id, 'Choose the one you want to cancel', buttons)
    else:
        page.send(sender_id, 'No booking record found for you')
        print('no booking record found', sender_id)

@page.callback([CONFIRM_CANCEL_MY_BOOKING + '_(.+)'])
def callback_3(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    evid = payload[len(CONFIRM_CANCEL_MY_BOOKING) + 1:]
    event = getEventById(evid)
    if not event:
        page.send(sender_id, 'No booking record found for you')
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
            page.send(sender_id, 'Failed to cancel the booking')
            print('Failed to cancel the booking', sender_id, event)
        else:
            page.send(sender_id, 'Your booking on %s was canclled.'%(bookingDatetime))
            print('Booking canceled successfully', sender_id, event)

@page.callback([MAKE_A_BOOKING])
def callback_4(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    buttons = []
    titles = ['This week', 'Next week', 'Week after next', 'Week after next 2', 'Next month']
    for i in range(5):
        buttons.append({
            "type": "postback",
            "value": CHOOSE_A_WEEK + '_' + str(i),
            "title": titles[i]
        })
    sendButtons(sender_id, 'Please choose', buttons)

@page.callback([CHOOSE_A_WEEK + r'_(\d)'])
def callback_5(payload, event):
    sender_id = event.sender_id
    print(payload, sender_id)
    n = int(payload[len(CHOOSE_A_WEEK) + 1:])
    if n < 4:
        # week
        t = datetime.utcnow() + timedelta(weeks=n)
        weekdays = getWeekDays(t)
        buttons = [{"type": "postback", "value": CHOOSE_A_DAY + '_' + str(toTimestamp(v)), "title": v.strftime('%a (%m-%d)')} for v in weekdays]
        sendButtons(sender_id, 'Please choose', buttons)
    else:
        # next month
        page.send(sender_id, 'Please input the date as MM-DD 3-25')
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
    cache.set(sender_id + '_date', str(toTimestamp(dt)), timeout=60 * 60)
    page.send(sender_id, 'Please input the time as hh:mm (24hour) 14:30')

def setTime(timeList, event):
    sender_id = event.sender_id
    print('set time', sender_id)
    t = cache.get(sender_id + '_date')
    if not t:
        page.send(sender_id, 'Please set date before set time')
        return
    dt = toDatetime(int(t))
    h, m = timeList
    dt = dt.replace(hour=h, minute=m, second=0, microsecond=0)
    rows = getSheetData()
    if rows:
        row = findRowByFbid(rows,sender_id)
        if not row:
            page.send(sender_id, 'Cant found record with your id')
            return
        createEvent('%s %s (%s)' %(row[0], row[1], row[2]), dt)
        page.send(sender_id, 'Thank you! Your booking was made successfully')

    
@page.after_send
def after_send(payload, response):
    """:type payload: fbmq.Payload"""
    print("complete")

# bootstrap app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True, threaded=True)
