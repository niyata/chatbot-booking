## make sure oauth2client==3.0.0 https://stackoverflow.com/questions/40154672/importerror-file-cache-is-unavailable-when-using-python-client-for-google-ser
please make sure config is right(config.py)  

# install dependencies
pip install -r requirements.txt
# write dependencies to requirements.txt
pip freeze > requirements.txt

### reset credentials when first run with your google account
python get_credentials.py --noauth_local_webserver

### run server for google sheet and user sms link
```sh
# run(test)
python run.py
# run(background)
gunicorn run:app -p .pid -D -c gunicorn-config.py
gunicorn run:app -c gunicorn-config.py
gunicorn --config=gunicorn-config.py run:app
# kill background
kill `cat .pid`
```

### schedule

**run in background:**
```sh
# run(test)
python schedule.py
# run(background)
nohup python schedule.py &
# kill background
kill $(ps aux | grep '[p]ython schedule.py' | awk '{print $2}')
```
