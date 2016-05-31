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

# time to pay ... now for real
@auth.requires_login()
def buy():
    if not session.cart:
       session.flash = 'Add something to shopping cart'
       redirect(URL('index'))
    import uuid
    from gluon.contrib.AuthorizeNet import process
    invoice = str(uuid.uuid4())
    total = sum(db.product(id).price*qty for id,qty in session.cart.items())
    form = SQLFORM.factory(
               Field('creditcard',default='4427802641004797',requires=IS_NOT_EMPTY()),
               Field('expiration',default='12/2012',requires=IS_MATCH('\d{2}/\d{4}')),
               Field('cvv',default='123',requires=IS_MATCH('\d{3}')),
               Field('shipping_address',requires=IS_NOT_EMPTY()),
               Field('shipping_city',requires=IS_NOT_EMPTY()),
               Field('shipping_state',requires=IS_NOT_EMPTY()),
               Field('shipping_zip_code',requires=IS_MATCH('\d{5}(\-\d{4})?')))                           
    if form.accepts(request,session):
        if process(form.vars.creditcard,form.vars.expiration,
                   total,form.vars.cvv,0.0,invoice,testmode=True):
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
                               shipping_zip_code = form.vars.shipping_zip_code)
            session.cart.clear()          
            session.flash = 'Thank you for your order'
            redirect(URL('invoice',args=invoice))               
        else:
            response.flash = "payment rejected (please call XXX)"
    return dict(cart=session.cart,form=form,total=total)

# an action to add and remove items from the shopping cart
def cart_callback():
    id = int(request.vars.id)
    if request.vars.action == 'add':
        session.cart[id]=session.cart.get(id,0)+1    
    if request.vars.action == 'sub':
        session.cart[id]=max(0,session.cart.get(id,0)-1)
    return str(session.cart[id])

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
