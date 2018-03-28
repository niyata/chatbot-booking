# important .py auto restart when app exit, so supervisor neend't restart it

## make sure oauth2client==3.0.0 https://stackoverflow.com/questions/40154672/importerror-file-cache-is-unavailable-when-using-python-client-for-google-ser
please make sure config is right(config.py)  

# install dependencies
pip install -r requirements.txt
# write dependencies to requirements.txt
pip freeze > requirements.txt

### reset credentials when first run with your google account
python get_credentials.py --noauth_local_webserver

### quick run all in background
sh restart-all.sh

### run server for google sheet and user sms link
```sh
# run(test)
python run.py
# run(background)
sudo supervisorctl start tornado-server
# kill background
sudo supervisorctl stop tornado-server
```

### schedule

```sh
# run(test)
python schedule.py
# run(background)
sudo supervisorctl start schedule
# kill background
sudo supervisorctl stop schedule
```

## about supervisord
```sh
# config file is /etc/supervisor/supervisord.conf /etc/supervisor/conf.d/chatbot-booking.conf
# start supervisord. start supervisord won't stop old process, pls search old process and kill them
sudo supervisord -c /etc/supervisor/supervisord.conf
# reload supervisor(if config changed, you need reload supervisord)
sudo supervisorctl reload
# start tornado-server(run.py)
sudo supervisorctl start tornado-server
# start schedule
sudo supervisorctl start schedule
# more
sudo supervisorctl start/restart/stop program-name(defined in config)
```

## datebase cassandra
```sh
# create keyspace
CREATE KEYSPACE chatbot_booking WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 3};
# make tables
python sync_tables.py
```