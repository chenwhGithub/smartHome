#!/usr/bin/env python
# -*- coding: utf8 -*-

class Execute:

    def __init__(self):
        self.procedures = {}
        self.notHittedCallback = None

    def registerProcedure(self, cmd, callback):
        self.procedures[cmd] = callback

    def registerNotHittedProcedure(self, callback):
        self.notHittedCallback = callback

    def process(self, cmd):
        hitted = False
        for k, v in self.procedures.items():
            if any(word in cmd for word in k):
                if len(v) > 1: # need to parse parameters from cmd
                    paras = v[1](cmd)
                    if isinstance(paras, tuple): # multi parameters, return tuple
                        v[0](*paras)
                    elif isinstance(paras, dict): # multi parameters, return dict, reserved
                        v[0](**paras)
                    else: # one parameter
                        v[0](paras)
                else: # no parameter
                    v[0]()
                hitted = True
                break

        if not hitted and self.notHittedCallback:
            self.notHittedCallback(cmd)
