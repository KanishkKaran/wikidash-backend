# Gunicorn configuration file
bind = "0.0.0.0:10000"
workers = 2
timeout = 120  # Increase timeout for complex queries
