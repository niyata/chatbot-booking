
# stop supervisord
sudo unlink /var/run/supervisor.sock
# config file is /etc/supervisor/supervisord.conf /etc/supervisor/conf.d/chatbot-booking.conf
# start supervisord(if config changed, you need stop and start supervisord)
sudo supervisord -c /etc/supervisor/supervisord.conf
# start tornado-server(run.py)
sudo supervisorctl start tornado-server
echo 'it is right if you get tornado-server: ERROR (spawn error)'
# start schedule
sudo supervisorctl start schedule
echo 'now it will visit https://knode.co:8083/ to check if app is running. Make sure the output is like Hello World!'
curl https://knode.co:8083/