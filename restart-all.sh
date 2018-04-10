# start tornado-server(run.py)
sudo supervisorctl restart cb-tornado
# start schedule
sudo supervisorctl restart cb-schedule
echo 'now it will visit https://knode.co:8083/ to check if app is running. Make sure the output is like Hello World!'
curl https://knode.co:8083/