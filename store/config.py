# address to listen on
addr = ('', 8000)

# directory to store information
dir = '/var/lib/store'

# log locations
log = '/var/log/store/store.log'
http_log = '/var/log/store/http.log'

# template directory to use
import os.path
template = os.path.dirname(__file__) + '/html'

# maximum file size
max_size = 33554432  # 32 MB

# minute of hour to prune files
minute = 9

# number of random characters to use
random = 6
