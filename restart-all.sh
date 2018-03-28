
# stop supervisord
sudo unlink /var/run/supervisor.sock
# config file is /etc/supervisor/supervisord.conf /etc/supervisor/conf.d/chatbot-booking.conf
# start supervisord(if config changed, you need stop and start supervisord)
sudo supervisord -c /etc/supervisor/supervisord.conf
# start tornado-server(run.py)
sudo supervisorctl start tornado-server
# start schedule
sudo supervisorctl start schedule