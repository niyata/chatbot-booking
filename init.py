import logging
logging.basicConfig(level=logging.ERROR)
from cassandra.cqlengine import connection
import config
 
# connect databse
try:
    connection.setup([config.db_host], config.db_keyspace, lazy_connect=True)
    print("Make connection to DB lazily")
except Exception as e:
    print("Error: connection db failed")
    logging.exception("Error: connection db failed")