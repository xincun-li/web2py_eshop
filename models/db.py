import datetime
from gluon.contrib.appconfig import AppConfig
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),
             check_reserved=['all'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
service = Service()
plugins = PluginManager()

# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
auth.define_tables(username=False, signature=False)

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# Start definition of database

CURRENCY = '$'
INE = IS_NOT_EMPTY()

session.cart = session.cart or {}
# Adding Admin Role
auth.settings.extra_fields['auth_user'] = [
    Field('is_admin','boolean',default=True)
]
auth.define_tables(username=False, signature=False)
if auth.user: auth.user.is_admin = True


db.define_table(
    'product',
    Field('category'),
    Field('name',required=True),
    Field('price','double'),
    Field('in_stock','boolean'),
    Field('quantity','integer'),
    Field('image','upload'),
    Field('tax_rate','double',default=11.25),
    Field('shipping','double',default=4.99),
    Field('create_date','datetime',default=datetime.datetime.now()),
    auth.signature,
    format='%(name)s')


def group_rows(rows,table1,*tables):
    last = None
    new_rows = []
    for row in rows:
        row_table1 = row[table1]
        if not last or row_table1.id!=last.id:
            last = row_table1
            new_rows.append(last)
            for t in tables:
                last[t] = []
        for t in tables:
            last[t].append(row[t])
    return new_rows
## create admin user, groups and role
if db(db.auth_group).count() == 0:
    admin = db.auth_group.insert(role='admin')
    db.auth_group.insert(role='customer')
    admin_user = db.auth_user.insert(email='lixincun@gmail.com', password=db.auth_user.password.validate('admin')[0])
    db.auth_membership.insert(group_id=admin, user_id=admin_user)
