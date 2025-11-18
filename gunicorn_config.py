# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '/home/user/privacy_auth/logs/access.log'
errorlog = '/home/user/privacy_auth/logs/error.log'
loglevel = 'info'

# Process naming
proc_name = 'privacy_auth_rc'

# Server mechanics
daemon = False
pidfile = '/home/user/privacy_auth/rc.pid'
