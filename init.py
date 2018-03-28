import logging
logging.basicConfig(level=logging.ERROR)
from cassandra.cqlengine import connection
import config
 
# connect databse
try:
    # lbp = None Cluster.__init__ called with contact_points specified, but no load_balancing_policy. In the next major version, this will raise an error; please specify a load-balancing policy.
    connection.setup([config.db_host], config.db_keyspace, lazy_connect=True)
    print("Make connection to DB lazily")
except Exception as e:
    print("Error: connection db failed")
    logging.exception("Error: connection db failed")