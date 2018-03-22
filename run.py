from flask import Flask, request
from config import TIMEZONE, SPREADSHEETID, fb_PAGE_ACCESS_TOKEN, fb_VERIFY_TOKEN
from utils import createEvent, getGoogleSheetService
from datetime import datetime
from fbmq import Page

# fbmq page
page = Page(fb_PAGE_ACCESS_TOKEN)

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
        events = []
        for row in values[1:]:
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
                time = time.replace(month= m, day=d, year=y, hour=int(row[5]), minute=int(row[6]), second=0)
                events.append(['%s %s (%s)'%(row[0], row[1], row[2]), time, float(row[7])])
                row[4] = ''
                row[5] = ''
                row[6] = ''
                row[7] = ''
        #
        for value in events:
            createEvent(*value)
        # save cleared
        if len(events) > 0:
            body = {
                'values': values
            }
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheetId, range=rangeName,
                valueInputOption='USER_ENTERED', body=body).execute()
            print('{0} cells updated.'.format(result.get('updatedCells')));
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

@page.handle_message
def message_handler(event):
  """:type event: fbmq.Event"""
  sender_id = event.sender_id
  # message = event.message_text
  # page.send(sender_id, "thank you! your message is '%s'" % message)
  message({
    "attachment":{
      "type":"template",
      "payload":{
        "template_type":"button",
        # "text":"What do you want to do next?",
        "buttons":[
            {
                "type":"web_url",
                "url":"https://www.messenger.com",
                "title":"View my booking"
            },
            {
                "type":"web_url",
                "url":"https://www.messenger.com",
                "title":"Cancel my booking"
            },
            {
                "type":"web_url",
                "url":"https://www.messenger.com",
                "title":"Make a booking"
            },
        ]
      }
    }
  })
  page.send(sender_id, message)

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
              rangeName = 'Sheet1!D%s:D%s'%(rowIndex, rowIndex)
              result = service.spreadsheets().values().update(
                  spreadsheetId=spreadsheetId, range=rangeName,
                  valueInputOption='USER_ENTERED', body=body).execute()
              print('facebook id stored in google sheet')
      else:
          print('no record found with given phone')
  print('no ref(phone) in hook event')

@page.after_send
def after_send(payload, response):
  """:type payload: fbmq.Payload"""
  print("complete")

# bootstrap app
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8082, debug=True, threaded=True)
