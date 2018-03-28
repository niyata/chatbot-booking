from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.models import Model

class user(Model):
    # facebookid
    id      = columns.Text(required=True, partition_key=True)

    locale      = columns.Text(required=False, )
    cache      = columns.Text(required=True, )

# this func will auto create tables
# coonect database before do this
def sync_tables():
    # tables
    sync_table(user)
