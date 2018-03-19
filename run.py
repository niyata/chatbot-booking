from flask import Flask, request
from config import TIMEZONE, SPREADSHEETID
from utils import createEvent, getGoogleSheetService
from datetime import datetime

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

# bootstrap app
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8081, debug=True, threaded=True)
