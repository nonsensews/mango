# -*- coding: utf-8 -*-
'''
    Mango system logic functions.
'''

# This file is part of mango.

# Distributed under the terms of the last AGPL License. 
# The full license is in the file LICENCE, distributed as part of this software.

__author__ = 'Jean Chassoul'


import zmq

from zmq.eventloop import ioloop, zmqstream

import time
import random

import logging
import base64


def basic_authentication(handler_class):
    '''
        @basic_authentication

        HTTP Basic Authentication Decorator
    '''

    def wrap_execute(handler_execute):
        '''
            Wrap Execute basic authentication function
        '''

        def basic_auth(handler, kwargs):
            '''
                Basic AUTH implementation
            '''
            auth_header = handler.request.headers.get('Authorization')
            if auth_header is None or not auth_header.startswith('Basic '):
                handler.set_status(403)
                handler.set_header('WWW-Authenticate', 'Basic '\
                                   'realm=mango') # get realm for somewhere else.
                handler._transforms = []
                handler.finish()
                return False
            auth_decoded = base64.decodestring(auth_header[6:])
            handler.username, handler.password = auth_decoded.split(':', 2)
            logging.info('Somewhere %s enter the dungeon! /api/ @basic_authentication' % handler.username)
            return True

        def _execute(self, transforms, *args, **kwargs):
            '''
                Execute the wrapped function
            '''
            if not basic_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)

    return handler_class

def get_command(message):
    '''
        get_command system function
    '''
    logging.warning('Received control command: {0}'.format(message))
    if message[0] == "Exit":
        logging.warning('Received exit command, client will stop receiving messages')
        should_continue = False
        ioloop.IOLoop.instance().stop()
        
def process_message(message):
    logging.warning("Processing ... {0}".format(message))

def server_router(port="5560"):
    '''
        ROUTER process
    '''
    pass

def gen_daemon(server_router):
    '''
        OTP gen_server analogy
    '''
    pass

def server_push(port="5556"):
    '''
        PUSH process
    '''
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:%s" % port)
    logging.warning("Running server on port: {0}".format(port))
    message = 'Continue'
    # serves only 5 request and dies
    while message == 'Continue':
        socket.send(message)
        time.sleep(1)
    socket.send("Exit")

def server_pub(port="5558"):
    '''
        PUB process
    '''
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    publisher_id = random.randrange(0,9999)
    logging.warning("Running PUB server process on port: {0}".format(port))
    logging.warning("serves only 5 request and dies")

    for reqnum in range(10):
        # Wait for next request from client
        topic = random.randrange(8,10)
        
        messagedata = "server#{0}".format(publisher_id)
        message = "{0} {1}".format(topic, messagedata)
        logging.warning(message)
        socket.send(message)
        time.sleep(1)

def client_dealer(por="5559"):
    '''
        DEALER process
    '''
    pass

def client(port_push, port_sub):
    '''
        Client process
    '''
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    stream_pull = zmqstream.ZMQStream(socket_pull)
    stream_pull.on_recv(get_command)
    print("Connected to server with port %s" % port_push)

    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect ("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt(zmq.SUBSCRIBE, "9")
    stream_sub = zmqstream.ZMQStream(socket_sub)
    stream_sub.on_recv(process_message)
    print("Connected to publisher with port %s" % port_sub)

    ioloop.IOLoop.instance().start()
    print("Worker has stopped processing messages.")

def spawn(message):
    '''
        Spawn process, return new uuid
    '''
    print("Spawn process {0}".format(message))

def link(message):
    '''
        Link processes
    '''
    print("Link processes {0}".format(message))

def spawn_link(message):
    '''
        Spawn link processes
    '''
    print("Spawn new process, {0} return Received process uuid".format(message))

def monitor(message):
    '''
        Monitor processes
    '''
    print("Monitor processes {0}".format(message))

def spawn_monitor(message):
    '''
        Spawn monitor processes
    '''
    print("Spawn new process, {0} return Received process uuid".format(message))

def register(message):
    '''
        Register process uuid
    '''
    print("Received message: %s" % message)

def context_switch(message):
    '''
        Node context switch
    '''
    print("talk between nodes")