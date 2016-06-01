# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------
import json
import socket
import struct
import datetime

#if not session.cart:
#    session.cart, session.balance = [], 0
@auth.requires_login()
def account():
    form=auth.profile()
    order_list = db(db.sale.buyer == auth.user.id).select()
    return dict(profile=form, order_list=order_list)

def index():
    now = datetime.datetime.now()
    span = datetime.timedelta(days=10)
    product_list = db((db.product.create_date >= (now-span)) | db.product.in_stock == True).select(limitby=(0, 100), orderby=~db.product.create_date)
    return locals()

@auth.requires_membership('admin')
def product():
    grid = SQLFORM.grid(db.product)
    return locals()

def cart():
    id = int(request.vars.id)
    if request.vars.action == 'add':
        session.cart[id] = session.cart.get(id, 0) + 1
    if request.vars.action == 'remove':
        session.cart[id] = max(0, session.cart.get(id, 0) - 1)
    redirect(URL('checkout'))

def checkout():
    order = []
    balance = 0

    for product_id, qty in session.cart.items():
        product = db(db.product.id == product_id).select().first()
        total_price = qty*product.price
        order.append((product_id, qty, total_price, product))
        balance += total_price
    session.balance = balance

    button1 = A(T('Continue shopping'), _href=URL('default', 'index'))
    button2 = A(T('Buy'), _href=URL('select_address'))
    return dict(order=order, balance=balance)

def remove_from_cart():
    del session.cart[int(request.vars.id)]
    redirect(URL('checkout'))


@auth.requires_login()
def select_address():
    addresses = db(db.address.user_id == auth.user.id).select()

    adrs = []
    for address in addresses:
        adrs.append(address.address+', '+ address.contact_name)

    form = SQLFORM.factory(
        Field('address', requires=IS_IN_SET(adrs))
        )
    if form.accepts(request.vars):
        session.address = form.vars.address
        redirect(URL('default', 'buy'))

    button = A(T('New address'), _href=URL('create_address'))
    return dict(addresses=addresses, button=button, form=form)

@auth.requires_login()
def create_address():
    db.address.user_id.default = auth.user.id
    db.address.user_id.readable = db.address.user_id.writable = False

    form = SQLFORM(db.address)
    if form.process().accepted:
        if session.cart and session.balance != 0:
            redirect(URL('default', 'select_address'))
        else:
            redirect(URL('default', 'index'))
    return dict(form=form)


# time to pay ... now for real
@auth.requires_login()
def buy():
    if not session.cart:
       session.flash = 'Add something to shopping cart'
       redirect(URL('index'))
    import uuid
    #from gluon.contrib.AuthorizeNet import process
    invoice = str(uuid.uuid4())
    total = sum(db.product(id).price*qty for id,qty in session.cart.items())
    form = SQLFORM.factory(
               Field('creditcard',default='1234567887654321',requires=IS_NOT_EMPTY()),
               Field('expiration',default='06/2016',requires=IS_MATCH('\d{2}/\d{4}')),
               Field('cvv',default='999',requires=IS_MATCH('\d{3}')),
               Field('shipping_address',requires=IS_NOT_EMPTY()),
               Field('shipping_city',requires=IS_NOT_EMPTY()),
               Field('shipping_state',requires=IS_NOT_EMPTY()),
               Field('shipping_zip_code',requires=IS_MATCH('\d{5}(\-\d{4})?')))                           
    if form.accepts(request,session):
        #if process(form.vars.creditcard,form.vars.expiration,
        #           total,form.vars.cvv,0.0,invoice,testmode=True):
            for key, value in session.cart.items():
                db.sale.insert(invoice=invoice,
                               buyer=auth.user.id,
                               product = key,
                               quantity = value,
                               price = db.product(key).price,
                               creditcard = form.vars.creditcard,
                               shipping_address = form.vars.shipping_address,
                               shipping_city = form.vars.shipping_city,
                               shipping_state = form.vars.shipping_state,
                               create_date = datetime.datetime.now,
                               shipping_zip_code = form.vars.shipping_zip_code)
                product_quantity = db(db.product.id == key).select().first()
                product_quantity.update_record(quantity = max(0, product_quantity.quantity - value))

            session.cart.clear()          
            session.flash = 'Thank you for your order'
            redirect(URL('invoice',args=invoice))
    return dict(cart=session.cart,form=form,total=total)

@auth.requires_login()
def invoice():
    return dict(invoice=request.args(0))

@auth.requires_login()
def product_detail():
    try:
        int(request.vars.id)
    except ValueError:
        raise HTTP(404, 'Product not found. Invalid ID.')

    id = int(request.vars.id)
    product = db(db.product.id == id).select().first()
    reviews = db(db.review.product == product.id).select()

    form = SQLFORM.factory(
        Field('review_content', 'text', default='Fantastic product!'),
        _class="form-inline"
        )
    if form.accepts(request.vars, session):
        db.review.insert(review_content=form.vars.review_content,
                            product=id,
                            author=auth.user.id, 
                            create_date=datetime.datetime.now())

    return dict(product=product, reviews=reviews, form=form)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
