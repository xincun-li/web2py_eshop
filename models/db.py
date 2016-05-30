# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

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

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# customer address
db.define_table('address',
    Field('user_id', 'reference auth_user', label=T('User')),
    Field('receiver', label=T('Addressee')),
    Field('adr_shipping', 'boolean', default=False, label=T('Shipping Address')),
    Field('zip_code', 'integer', label=T('Zip Code')),
    Field('address', label=T('Address')),
    Field('adr_number', 'integer', label=T('Number')),
    Field('complement', label=T('Complement')),
    Field('neighborhood', label=T('Neighborhood')),
    Field('city', label=T('City')),
    Field('adr_state', label=T('State'))
    )

## validators
db.address.user_id.requires = IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')
db.address.receiver.requires = IS_NOT_EMPTY()
db.address.address.requires = IS_NOT_EMPTY()
db.address.adr_number.requires = IS_NOT_EMPTY()
db.address.neighborhood.requires = IS_NOT_EMPTY()
db.address.city.requires = IS_NOT_EMPTY()
db.address.adr_state.requires = IS_NOT_EMPTY()

# categories
db.define_table('category',
    Field('name', label=T('Name')),
    Field('description', 'text', label=T('Description')),
    Field('parent_category', 'integer'),
    format = '%(name)s'
    )
## validators
db.category.name.requires = IS_NOT_EMPTY()
db.category.parent_category.requires = IS_EMPTY_OR(IS_IN_DB(db, 'category.id','%(name)s'))

# carriers
db.define_table('carrier',
    Field('name', label=T('Name')),
    Field('description', 'text', label=T('Description')),
    format = '%(name)s'
    )

db.define_table('carrier_tax',
    Field('name', label=T('Name')),
    Field('tax', 'decimal(7,2)', label=T('Tax')),
    Field('carrier_id', 'reference carrier', label=T('Carrier ID')),
    format = '%(name)s'
    )
db.carrier_tax.carrier_id.requires = IS_IN_DB(db, 'carrier.id','%(name)s')

# suppliers
db.define_table('supplier',
    Field('name', label=T('Name')),
    Field('business_name', label=T('Business Name')),
    Field('phone', label=T('Phone')),
    Field('email', label=T('Email')),
    Field('address', label=T('Address')),
    Field('federal_id', label=T('Federal Id')),
    Field('state_id', label=T('State Id')),
    Field('info', 'text', label=T('Supplier Info')),
    format = '%(name)s'
    )
## validators
db.category.name.requires = IS_NOT_EMPTY()
db.category.parent_category.requires = IS_EMPTY_OR(IS_IN_DB(db, 'category.id','%(name)s'))

# products
db.define_table('product',
    Field('name', label=T('Name')),
    Field('short_description', length=256, label=T('Short description')),
    Field('description', 'text', label=T('Description')),
    Field('price', 'decimal(7,2)', default=0, label=T('Price')),
    Field('tax', 'decimal(7,2)', default=0, label=T('Tax')),
    Field('product_stok', 'integer', default=0, label=T('Quantity')),
    Field('featured_image', 'upload', label=T('Featured Image')),
    Field('default_category', 'reference category', label=T('Default Category')),
    Field('default_supplier', 'reference supplier', label=T('Default Supplier')),
    auth.signature,
    format = '%(name)s'
    )
db.product.default_category.requires = IS_IN_DB(db, 'category.id','%(name)s')
db.product.default_supplier.requires = IS_IN_DB(db, 'supplier.id','%(name)s')

## validators
db.product.name.requires = IS_NOT_EMPTY()

# product category
db.define_table('product_category',
    Field('product_id', 'reference product'),
    Field('category_id', 'reference category')
    )
db.product_category.product_id.requires = IS_IN_DB(db, 'product.id', '%(name)s')
db.product_category.category_id.requires = IS_IN_DB(db, 'category.id', '%(name)s')

#product images
db.define_table('product_images',
    Field('image', 'upload'),
    Field('product_id', 'reference product'),
    )
#db.product_image.product_id.requires = IS_IN_DB(db, 'product.id', '%(name)s')

#product stok
db.define_table('product_stok',
    Field('product_id', 'reference product'),
    Field('quantity', 'integer'),
    Field('min_quantity', 'integer'),
    )
db.product_stok.product_id.requires = IS_IN_DB(db, 'product.id', '%(name)s')
db.product_stok.quantity.requires = IS_NOT_EMPTY()
db.product_stok.min_quantity.requires = IS_NOT_EMPTY()

# products specifications
db.define_table('specification',
    Field('product', 'reference product', unique=True, label=T('Product')),
    Field('processor', label=T('Processor')),
    Field('weight', 'double', label=T('Weight (kg)')),
    Field('memory', label=T('Memory')),
    Field('dimensions', label=T('Dimensions (W x D x H)(cm)')),
    Field('esp_storage', label=T('Storage')),
    Field('ethernet', label=T('Ethernet')),
    Field('battery', label=T('Battery')),
    Field('other', 'text', label=T('Other')),
    format = '%(product.name)s'
    )
## validators
db.specification.product.requires = IS_IN_DB(db, 'product.id', '%(name)s')

db.define_table('order_status',
    Field('status_text'),
    )

db.define_table('product_order',
    Field('user_id', 'reference auth_user'),
    Field('order_date', 'datetime'),
    Field('order_carrier', 'reference carrier'),
    Field('order_carrier_tax'),
    Field('order_value'),
    Field('order_status_id', 'reference order_status'),
    )

db.define_table('order_item',
    Field('item_name'),
    Field('item_quantity'),
    Field('item_value', 'decimal(7,2)'),
    Field('item_total_value', 'decimal(7,2)'),
    )

db.define_table('order_history',
    Field('order_history_date', 'datetime'),
    Field('order_id', 'reference product_order'),
    Field('order_history_description'),
    )

# reviews
db.define_table('review',
    Field('product', 'reference product'),
    Field('rv_message', 'text'),
    auth.signature
    )

# config
db.define_table('info',
    Field('name', label=T('Name')),
    Field('address', label=T('Address')), 
    Field('city', label=T('City')), 
    Field('state_uf', label=T('State')), 
    Field('zip_code', label=T('Zip Code')), 
    Field('phone', label=T('Phone')), 
    Field('fax', label=T('Fax')), 
    Field('email', label=T('Email')),
    Field('logo', 'upload', default='', label=T('Logo')),
    format = '%(name)s'
    )
## create unique record
if db(db.info).count() == 0:
    store = db.info.insert(name='Store name')
else:
    store = db(db.info).select().first()
## validators
db.info.name.requires = IS_NOT_EMPTY()
db.info.email.requires = IS_EMAIL()
db.info.logo.requires = IS_EMPTY_OR(IS_IMAGE())
# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)