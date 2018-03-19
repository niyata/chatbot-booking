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
            if row[4] and row[5] and row[6] and row[7]:

                time = datetime.strptime(row[4], '%y-%m-%d')
                time = time.replace(hour=int(row[5]). minute=int(row[6]))
                events.append(['%s %s (%s)'%(row[0], row[1], row[2]), time, float(row[7])])
                row[4] = ''
                row[5] = ''
                row[6] = ''
                row[7] = ''
        # save cleared
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheetId, range=rangeName,
            valueInputOption='RAW', body=body).execute()
        print('{0} cells updated.'.format(result.get('updatedCells')));
        #
        for value in events:
            createEvent(*value)

# bootstrap app
if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8081', debug=True, threaded=True)
