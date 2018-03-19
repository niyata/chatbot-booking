from get_google_calendar_credentials import get_google_calendar_credentials
from get_google_sheet_credentials import get_google_sheet_credentials


if __name__ == '__main__':
    import os
    import shutil
    from utils import p, pj
    dirp = p('credentials')
    if os.path.exists(dirp):
        shutil.rmtree(dirp)
    get_google_calendar_credentials()
    get_google_sheet_credentials()
