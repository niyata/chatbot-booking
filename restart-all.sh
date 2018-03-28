# start tornado-server(run.py)
sudo supervisorctl restart tornado-server
echo 'it is right if you get tornado-server: ERROR (spawn error)'
# start schedule
sudo supervisorctl restart schedule
echo 'now it will visit https://knode.co:8083/ to check if app is running. Make sure the output is like Hello World!'
curl https://knode.co:8083/