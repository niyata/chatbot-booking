import logging
datefmt = '%Y-%m-%d %H:%M:%S'
format_str = '%(asctime)s %(levelname)s %(message)s '
logging.basicConfig(level=logging.WARN, format=format_str, datefmt=datefmt)
from cassandra.cqlengine import connection
import config
 
# connect databse
try:
    connection.setup([config.db_host], config.db_keyspace, lazy_connect=True)
    print("Make connection to DB lazily")
except Exception as e:
    print("Error: connection db failed")
    logging.exception("Error: connection db failed")