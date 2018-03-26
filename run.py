from flask import Flask, request
from config import TIMEZONE, SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, fb_VERIFY_TOKEN
from utils import createEvent, getGoogleSheetService, getEventsByPhone, getBookingDateFromEvent
from utils import getSheetValues,findRow, findRowByFbid, getEventById
from datetime import datetime
from fbmq import Page, Template

# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)

# constant
VIEW_MY_BOOKING = 'VIEW_MY_BOOKING'
CANCEL_MY_BOOKING = 'CANCEL_MY_BOOKING'
CONFIRM_CANCEL_MY_BOOKING = 'CONFIRM_CANCEL_MY_BOOKING'
MAKE_A_BOOKING = 'MAKE_A_BOOKING'

# init app
app = Flask(__name__)

# actions


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/create-events")
def createEvents():
    spreadsheetId = SPREADSHEETID
    rangeName = 'Sheet1'
    service = getGoogleSheetService()
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        rows = values[1:]
        events = []
        for i, row in enumerate(rows):
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
            ev = createEvent(*value[:-1])
            i = value[-1]
            phone = rows[i][0]

        # save cleared
        if len(events) > 0:
            body = {
                'values': values
            }
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheetId, range=rangeName,
                valueInputOption='USER_ENTERED', body=body).execute()
            print('{0} cells updated.'.format(result.get('updatedCells')))
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


def send_buttons(sender_id):
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
    page.send(sender_id, Template.Buttons("hello", buttons))

@page.handle_message
def message_handler(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    # message = event.message_text
    # page.send(sender_id, "thank you! your message is '%s'" % message)
    print('receive msg', sender_id)
    send_buttons(sender_id)

@page.handle_referral
def handler2(event):
    """:type event: fbmq.Event"""
    sender_id = event.sender_id
    # page.send(sender_id, "thank you! your message is '%s'" % message)
    try:
        phone = event.referral['ref']
    except Exception as e:
        phone = None
    if ref:
        print('phone', phone)
        # get sheet
        service = getGoogleSheetService()
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
        row = findRow(phone)
        if row:
            if row[3]:
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
                result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheetId, range=rangeName,
                    valueInputOption='USER_ENTERED', body=body).execute()
                print('facebook id stored in google sheet')
        else:
            print('no record found with given phone')
    print('no ref(phone) in hook event')
    send_buttons(sender_id)

@page.callback([VIEW_MY_BOOKING])
def callback_1(payload, event):
    sender_id = event.sender_id
    print(CANCEL_MY_BOOKING, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        event = getEventsByPhone(row[0])[0]
        if not event:
            page.send(sender_id, 'No booking record found for you')
            print('no booking record found', sender_id)
        else:
            bookingDatetime = getBookingDateFromEvent(event)
            bookingInfo = 'Booking date: %s'%(bookingDatetime)
            page.send(sender_id, bookingInfo)
    else:
        page.send(sender_id, 'No booking record found for you')
        print('no booking record found', sender_id)

@page.callback([CANCEL_MY_BOOKING])
def callback_2(payload, event):
    sender_id = event.sender_id
    print(CANCEL_MY_BOOKING, sender_id)
    rows = getSheetValues()
    row = findRowByFbid(rows,sender_id)
    if row:
        events = getEventsByPhone(row[0])
        if not events:
            page.send(sender_id, 'No booking record found for you')
            print('no booking record found', sender_id)
        else:
            if len(events) == 1:
                bookingDatetime = getBookingDateFromEvent(event)
                bookingInfo = 'Booking date: %s'%(bookingDatetime)
                buttons = [
                    {
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": "Confirm to cancel my booking"
                    },
                ]
                page.send(sender_id, Template.Buttons(bookingInfo, buttons))
            else:
                buttons = []
                for event in events:
                    bookingDatetime = getBookingDateFromEvent(event)
                    bookingInfo = 'Booking date: %s'%(bookingDatetime)
                    buttons.append({
                        "type": "postback",
                        "value": CONFIRM_CANCEL_MY_BOOKING + '_' + str(event['id']),
                        "title": bookingInfo,
                    })
                page.send(sender_id, Template.Buttons('Confirm to cancel my booking', buttons))
    else:
        page.send(sender_id, 'No booking record found for you')
        print('no booking record found', sender_id)

@page.callback([CONFIRM_CANCEL_MY_BOOKING + '_(.w+)'])
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
        service.events().delete(calendarId='primary', eventId=event['id']).execute()
        page.send(sender_id, 'Your booking on %s was canclled.'%(bookingDatetime))

@page.after_send
def after_send(payload, response):
    """:type payload: fbmq.Payload"""
    print("complete")

# bootstrap app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True, threaded=True)
