# -*- coding: utf-8 -*-
'''
    Mango records
'''
# This file is part of mango.
#
# Distributed under the terms of the last AGPL License. The full
# license is in the file LICENCE, distributed as part of this
# software.

__author__ = 'Jean Chassoul'


import arrow

import pandas as pd

import uuid
import motor

from tornado import gen

from mango.models import records
from mango.models import reports

from mango.tools import clean_structure, clean_results


# functions vs class records?


class Records(object):
    '''
        Records resources
    '''
    
    @gen.engine
    def new_detail_record(self, struct, callback):
        '''
            Create a new record entry
        '''
        try:
            record = records.Record(struct)
            record.validate()
        except Exception, e:
            callback(None, e)
            return

        record = clean_structure(record)

        result = yield gen.Task(self.db.records.insert, record)
        result, error = result.args

        if error:
            callback(None, error)
            return
        
        callback(record.get('uuid'), None)


    @gen.engine
    def modify_record(self, struct, callback):
        '''
            Modify a existent record entry
        '''
        # patch implementation
        pass

    @gen.engine
    def replace_record(self, struct, callback):
        '''
            Replace a existent record entry
        '''
        # put implementation
        pass

    
    @gen.engine
    def get_detail_record(self, account, record_uuid, callback):
        '''
            Get a detail record
        '''
        try:
            if not account:
                record = yield motor.Op(self.db.records.find_one,
                                      {'uuid':record_uuid})
            else:
                record = yield motor.Op(self.db.records.find_one,
                                      {'uuid':record_uuid,
                                       'accountcode':account})
            if record:
                record = records.Record(record)
                record.validate()
        except Exception, e:
            recordback(None, e)
            return
        
        callback(record, None)
    
    
    @gen.engine
    def get_detail_records(self, account, start, stop, page_num, lapse, callback):
        '''
            Get detail records 
        '''
        page_num = int(page_num)
        page_size = self.settings['page_size']
        result = []
        
        if not account:
            query = self.db.records.find({'public':True})
        elif type(account) is list:
            accounts = [{'accountcode':a, 'assigned': True} for a in account]
            query = self.db.records.find({'$or':accounts})
        else:
            query = self.db.records.find({'accountcode':account,
                                        'assigned':True})
        
        query = query.sort([('_id', -1)]).skip(page_num * page_size).limit(page_size)
        
        try:
            for record in (yield motor.Op(query.to_list)):
                result.append(records.Record(record))

            struct = {'results': result}
            results = reports.BaseResult(struct)
            results.validate()
        except Exception, e:
            callback(None, e)
            return

        results = clean_results(results)

        callback(results, None)
        
    
    @gen.engine
    def get_unassigned_records(self, start, stop, page_num, lapse, callback):
        '''
            Get unassigned record detail records
        '''
        page_num = int(page_num)
        page_size = self.settings['page_size']
        result = []
        
        query = self.db.records.find({'assigned':False}) # or $exist = false ?

        # _id is from bson and mongodb engine
        # for a more independent implementation sort by uuid

        query = query.sort([('_id', -1)]).skip(page_num * page_size).limit(page_size)
        
        try:
            for record in (yield motor.Op(query.to_list)):
                result.append(records.Record(record))
            
            struct = {'results':result}

            results = reports.BaseResult(struct)
            results.validate()
        except Exception, e:
            callback(None, e)
            return

        results = clean_results(results)
        
        callback(results, None)

    @gen.engine
    def set_assigned_flag(self, account, record_uuid, callback):
        '''
            Set the assigned record flag

            This method set the assigned flag of a record record
        '''
        # bad stuff
        # print('account %s set assigned flag on %s' % account, record_id)

        try:
            result = yield motor.Op(self.db.records.update,
                                    {'uuid':record_uuid, 
                                     'accountcode':account}, 
                                    {'$set': {'assigned': True}})
        except Exception, e:
            callback(None, e)
            return
        
        callback(result, None)

    @gen.engine
    def get_summaries(self, account, start, stop, page_num, lapse, callback):
        '''
            Get stuff summaries
        '''

        if not start:
            start = arrow.utcnow()
        if not stop:
            stop = start.replace(days=+1)

        if lapse:
            print('given lapse:', lapse)


    @gen.engine 
    def get_summary(self, account, lapse, start, stop, callback):
        '''
            Get stuff summary
        '''
        # to avoid pain please learn how to use pytz
        # to be more awesome replace all datetime and pytz with the new arrow

        if not start:
            start = arrow.utcnow()
        if not stop:
            stop = start.replace(days=+1)

        start = start.timestamp
        stop = stop.timestamp

        
        print(start, stop, 'get summary')
        
        
        if lapse:
            print 'given lapse:', lapse

        # MongoDB aggregation match operator
        if type(account) is list:
            match = {
                'assigned':True,
                'start':{'$gte':start, '$lt':stop},
                '$or':[{'accountcode':a} for a in account]
            }
        else:
            match = {
                'accountcode':account, 
                'assigned': True,
                'start': {'$gte':start, '$lt': stop}
            }
        
        # MongoDB aggregation project operator
        project = {
            "_id" : 0,
            
            # record timestamps
            "start":1,
            "answer":1,
            "end":1,
            
            # record duration seconds
            "duration" : 1,
            # record billing seconds
            "billsec" : 1,
            
            # project id's timestamp stuff?
            "year" : {  
                "$year" : "$start"
            },
            "month" : {  
                "$month" : "$start"
            },
            "week" : {  
                "$week" : "$start"
            },
            "day" : {
                "$dayOfMonth" : "$start"
            },
            "hour" : {
                "$hour" : "$start"
            },
            "minute" : {
                "$minute" : "$start"
            },
            "second" : {
                "$second" : "$start"
            }
        }

        # MongoDB aggregation group operator

        # R&D on group by accountcode

        group = {
            '_id': {
                'start': '$start',
                'answer': '$answer',
                'end': '$end',
                'year': '$year',
                'month': '$month',
                'week':'$week',
                'day': '$day',
                'hour':'$hour',
                'minute': '$minute',
                'second': '$second',
            },
            'records': {
                '$sum':1
            },
            'average': {
                '$avg':'$billsec'
            },
            'duration': {
                '$sum':'$duration'
            },
            'billing': {
                '$sum':'$billsec'
            }
        }

        # MongoDB aggregation pipeline
        pipeline = [
            {'$match':match},
            {'$project':project},
            {'$group':group}
        ]

        try:
            result = yield motor.Op(self.db.records.aggregate, pipeline)

        except Exception, e:
            callback(None, e)
            return

        callback(result['result'], None)

    
    @gen.engine
    def remove_record(self, record_uuid, callback):
        '''
            Remove a record entry
        '''
        try:
            result = yield motor.Op(self.db.records.remove,
                                    {'uuid':record_uuid})
        except Exception, e:
            callback(None, e)
            return

        callback(result, None)