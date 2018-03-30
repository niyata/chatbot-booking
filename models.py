from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.models import Model

class key_value(Model):
    key      = columns.Text(required=True, partition_key=True)
    value      = columns.Text(required=False, )
class user(Model):
    # facebookid
    id      = columns.Text(required=True, partition_key=True)

    locale      = columns.Text(required=False, )
    cache      = columns.Text(required=True, )


class client(Model):
    # line number
    id      = columns.Integer(required=True, partition_key=True)
    phone      = columns.Text(required=False, index = True)
    name      = columns.Text(required=False, index = True)
    full_name      = columns.Text(required=False, index = True)
    facebook_id      = columns.Text(required=False, index = True)

# this func will auto create tables
# coonect database before do this
def sync_tables():
    # tables
    sync_table(key_value)
    sync_table(user)
    sync_table(client)
