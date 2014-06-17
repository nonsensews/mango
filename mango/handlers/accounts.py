# -*- coding: utf-8 -*-
'''
    Mango HTTP accounts handlers.
'''

# This file is part of mango.

# Distributed under the terms of the last AGPL License.
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import motor

# import numpy as np
# import pandas as pd

from tornado import gen
from tornado import web

from mango.system import accounts
from mango.system import records

from mango.tools import content_type_validation
from mango.tools import check_json

from mango.tools import errors

from mango.handlers import BaseHandler


@content_type_validation
class UsersHandler(accounts.MangoAccounts, BaseHandler):
    '''
        User accounts HTTP request handlers
    '''

    @web.authenticated
    @web.asynchronous
    @gen.engine
    def get(self, account=None, page_num=0):
        '''
            Get user accounts
        '''
        account_type = 'user'
        if not account:
            # get list
            users = yield motor.Op(self.get_account_list, account_type, page_num)
            self.finish({'users':users})
        else:
            account = account.rstrip('/')
            result = yield motor.Op(self.get_account, account, account_type)
            if result:
                self.finish(result)
                return
            else:
                # let it crash
                self.set_status(400)
                self.finish({'missing':account})
                return

    @web.asynchronous
    @gen.engine
    def post(self):
        '''
            Create user account
        '''
        struct = yield motor.Op(check_json, self.request.body)
        struct['account_type'] = 'user'

        format_pass = (True if struct else False)
        if not format_pass:
            self.set_status(400)
            self.finish({'JSON':format_pass})
            return

        new_account = yield gen.Task(self.new_account, struct)
        result, error = new_account.args

        # handle SIP accounts out-of-band

        # momoko insert sip account
        #if result:
        #    sip_account = yield gen.Task(self.new_sip_account, struct)
        #    sip_result, sip_error = sip_account.args
        
        # missing post error handlers (if any)

        #else:
        #    self.set_status(400)
        #    self.finish({'errors':struct})
        #    return

        self.set_status(201)
        self.finish({'id':result})

    @web.authenticated
    @web.asynchronous
    @gen.engine
    def delete(self, account):
        '''
            Delete a user account
        '''
        account = account.rstrip('/')
        result = yield motor.Op(self.remove_account, account)

        # why we're using result['n']?

        import pprint
        pprint(result)
        print('''delete check result['n'] on UsersHandler''')

        if not result['n']:
            self.set_status(400)
            system_error = errors.Error('missing')
            error = system_error.missing('user', account)
            self.finish(error)
            return

        self.set_status(204)
        self.finish()


@content_type_validation
class OrgsHandler(accounts.Orgs, BaseHandler):
    '''
        Organization account resource handlers
    '''

    @web.authenticated
    @web.asynchronous
    @gen.engine
    def get(self, account=None, page_num=0):
        '''
            Mango organization accounts get handler
            
            Get organization accounts
        '''
        account_type = 'org'
        if not account:
            orgs = yield motor.Op(self.get_account_list, account_type, page_num) 
            self.finish({'orgs':orgs})
        else:
            account = account.rstrip('/')

            result = yield motor.Op(self.get_account, account, account_type)
            if result:
                self.finish(result)
                return
            else:
                self.set_status(400)
                self.finish({'missing':account})
                return

    @web.asynchronous
    @gen.engine
    def post(self):
        '''
            Create organization accounts
        '''
        current_user = self.get_current_user()
        
        if not current_user:
            current_user = 'capnkooc'
        
        struct = yield motor.Op(check_json, self.request.body)
        struct['account_type'] = 'org'

        org = struct['account']
        
        format_pass = (True if struct else False)
        if not format_pass:
            self.set_status(400)
            self.finish({'JSON':format_pass})
            return

        org_id = yield motor.Op(self.new_account, struct)
                
        team = {
            'name': 'owners',
            'permission': 'super',
            'members': [current_user]
        }

        print(org, team)

        check_member = yield motor.Op(self.new_member, org, current_user)
        check_team = yield motor.Op(self.new_team, org, team)

        print('team', check_team)
        print('member', check_member)
        print('org_id', org_id)

        if not org_id:
            print('some errors')
            self.set_status(400)
            self.finish({'errors':struct})
            return

        self.set_status(201)
        self.finish({'id':org_id})

    @web.authenticated
    @web.asynchronous
    @gen.engine
    def delete(self, account):
        '''
            Mango organization accounts delete handler
        
            Delete a organization account
        '''
        org = account.rstrip('/')
        # get members
        # each member in members remove member
        members = yield motor.Op(self.get_members, org)
        members = (members['members'] if members['members'] else False)
        
        # clean this hack
        
        for user in members:
            rmx = yield motor.Op(self.remove_member, org, user)
            
        # check_member = yield motor.Op(self.remove_member, org_id, current_user)
        
        result = yield motor.Op(self.remove_account, org)
        
        if not result['n']:
            self.set_status(400)
            system_error = errors.Error('missing')
            error = system_error.missing('org', org)
            self.finish(error)
            return

        self.set_status(204)
        self.finish()


@content_type_validation
class TeamsHandler(accounts.Orgs, BaseHandler):
    '''
        Teams resource handlers
    '''
    pass


@content_type_validation
class MembersHandler(accounts.Orgs, BaseHandler):
    '''
        Members resource handlers
    '''
    pass


@content_type_validation
class RecordsHandler(accounts.Accounts, records.Records, BaseHandler):
    '''
        Records resource handlers
    '''

    @web.authenticated
    @web.asynchronous
    @gen.engine
    def get(self, account, page_num=0):
        '''
            Retrieve records from accounts
        '''
        # check_type account with organizations
        #account_type = yield motor.Op(self.check_type, account, 'user')
        
        orgs = yield motor.Op(self.get_orgs_list, account)
        
        print(orgs, 'organizations')
        
        #if not account_type:
        #    system_error = errors.Error('invalid')
        #    self.set_status(400)
        #    error = system_error.invalid('user', account)
        #    self.finish(error)
        #    return

        print(account, page_num)

        result = yield motor.Op(self.get_record_list, 
                                account=account, 
                                page_num=page_num,
                                lapse=None,
                                start=None,
                                end=None)

        self.finish(result)
        
    @web.authenticated
    @web.asynchronous
    @gen.engine
    def post(self, account):
        '''
            Create a new record for the current logged account.
        '''
        result = yield gen.Task(check_json, self.request.body)
        struct, error = result.args
        if error:
            self.set_status(400)
            self.finish(error)
            return
        
        if account == self.get_current_user():
            struct['account'] = account
        
        # check if orgs follows the access pattern.
        
        else:
            self.set_status(404)
            self.finish({'WARNING':'Pre-Access patterns research'})
            return
        
        result = yield gen.Task(self.new_cdr, struct)
        record, error = result.args
        
        if record:

            # handle this out-of-band.

            struct = {'account':account,
                      'resource': 'records',
                      'id': record}

            res_args = yield gen.Task(self.new_resource, struct)

            update, res_error = res_args.args

            if res_error:
                print(res_error, 'WARNING: error on new_resource record.')

        if error:
            self.set_status(400)
            model = 'Records'
            reason = {'duplicates':[('Record', 'uniqueid'), (model, 'uuid')]}

            message = yield motor.Op(
                self.let_it_crash, 
                struct, 
                model, 
                error,
                reason
            )

            self.finish(message)
            return

        self.set_status(201)
        self.finish({'id':record})
    
    @web.authenticated
    @web.asynchronous
    def delete(self, account, record=None, page_num=0):
        '''
            delete
        '''
        pass
    
    @web.authenticated
    @web.asynchronous
    def put(self, account, record=None, page_num=0):
        '''
            put
        '''
        pass
    
    @web.authenticated
    @web.asynchronous
    def patch(self, account, record=None, page_num=0):
        '''
            patch
        '''
        pass


@content_type_validation
class RoutesHandler(accounts.Accounts, BaseHandler):
    '''
        Routes resource handlers
    '''
    
    @web.authenticated
    @web.asynchronous
    @gen.engine
    def get(self, account):
        # get account the record billing routes from the database
        routes = yield motor.Op(self.get_routes, account)
        self.finish(routes)
        
        
    #@web.authenticated
    @web.asynchronous
    @gen.engine
    def post(self, account):
        '''
            Create new record billing route
        '''
        
        result = yield gen.Task(check_json, self.request.body)
        struct, error = result.args
        if error:
            self.set_status(400)
            self.finish(error)
            return
        
        struct['account'] = account
        
        print(struct)
        
        result = yield motor.Op(self.new_route, struct)

        self.finish()