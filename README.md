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
# Reload config and then add and remove as necessary (restarts programs)
# reload supervisor(if config changed, you need reload supervisord)
# Restarts the applications whose configuration has changed.
# Note: After the update command, new application configurations becomes available to start, but do not start automatically until the supervisor service restarts or system reboots (even if autostart option is not disabled). In order to start new application, e.g app2, simply run: supervisorctl start app2
sudo supervisorctl update
# Restart application without making configuration changes available. It stops, and re-starts the application.
sudo supervisorctl start name
# Reload the daemon’s configuration files, without add/remove (no restarts)
# If you do not want to re-start all managed applications, but make your configuration changes available, use this command:
# This command only updates the changes. It does not restart any of the managed applications, even if their configuration has changed. New application configurations cannot be started, neither.
sudo supervisorctl reread
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