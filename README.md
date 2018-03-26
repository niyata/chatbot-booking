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
