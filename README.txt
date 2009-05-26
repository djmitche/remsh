Conversation
============

(OVER == turn change)

SL: { 'type' : 'register', 'hostname' : $hostname, 'version' : $version } OVER

# auth is up to SSL keys

# version is client version -- what ops are avail, etc.

# master can run whatever commands it wants to verify capabilities, or just
# key off hostname

MA: { 'type' : 'registered' }

# TODO: ping pong

# execute

# newop introduces an operation, opparam specifies parameters (which can
# be repeated), and startop starts it on the slave
MA: { 'type' : 'newop', 'op' : 'execute' }
MA: { 'type' : 'opparam', 'param' : 'arg', 'value' : $arg }
# ...
MA: { 'type' : 'startop' } OVER
# slave sends any file contents back as they fill buffers
SL: { 'type' : 'data', 'name' : $name, 'data' : $data }
# ...
SL: { 'type' : 'opdone', 'result' : $result } OVER

# set_cwd

MA: { 'type' : 'newop', 'op' : 'set_cwd'
MA: { 'type' : 'opparam', 'param' : 'cwd', 'value' : $new_cwd } # optional
MA: { 'type' : 'startop' } OVER
SL: { 'type' : 'opdone', 'cwd' : $new_cwd } OVER
# opparam missing -> revert to default cwd
# cwd missing in opdone -> directory not found

Slaves and Slave Environments
=============================

pkgspin doesn't need slave environments, but needs some way to reserve slaves
-- or is that higher-level?
