# This file is part of remsh.
#
# remsh is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# remsh is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with remsh.  If not, see <http://www.gnu.org/licenses/>.

from remsh.amp import wire

Error = wire.Error

class RemoteError(Exception):
    """An error sent directly from the remote system"""

class RPC(object):
    def __init__(self, wire):
        self.wire = wire
        self.counter = 1

    ##
    # Public interface

    def call_remote(self, method, **kwargs):
        return self._call_remote(method, True, kwargs)

    def call_remote_no_answer(self, method, **kwargs):
        return self._call_remote(method, False, kwargs)

    def handle_call(self):
        reqbox = self.wire.read_box()
        if '_ask' not in reqbox:
            raise Error("request box does not have an _ask key")
        ask_token = reqbox['_ask']
        del reqbox['_ask']

        if '_command' not in reqbox:
            raise Error("request box does not have a _command key")
        methname = 'remote_' + reqbox['_command']
        if not hasattr(self, methname):
            raise Error("unknown command %r" % reqbox['_command'])
        meth = getattr(self, methname)
        del reqbox['_command']

        try:
            respbox = meth(reqbox)
        except RemoteError, e:
            respbox = { '_error' : ask_token, '_error_description' : e.args[0], '_error_code' : '0' }
            self.wire.send_box(respbox)
            return

        if respbox:
            respbox['_answer'] = ask_token
            self.wire.send_box(respbox)

    ##
    # Implementation

    # TODO: add mutual exclusion here? or at the wire level? or at all?
    # -> probaby here, because counter is unprotected

    def _call_remote(self, method, expect_answer, arguments):
        ask = str(self.counter)
        self.counter += 1

        wirebox = arguments.copy()
        wirebox['_command'] = method
        wirebox['_ask'] = ask
        self.wire.send_box(wirebox)

        if not expect_answer: return

        respbox = self.wire.read_box()
        if '_answer' in respbox:
            if respbox['_answer'] != ask: raise Error("answer box does not correspond to the request")
            del respbox['_answer']
            return respbox
        elif '_error' in respbox:
            if respbox['_error'] != ask: raise Error("error box does not correspond to the request")
            raise RemoteError(repbox['_error_description'])
        else:
            raise Error("response has neither _answer nor _error keys")
