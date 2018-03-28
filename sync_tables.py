import config
from cassandra.cqlengine import connection
import models

connection.setup([config.db_host], config.db_keyspace, lazy_connect=True)
models.sync_tables()