#!/usr/bin/env python

import os
import sys
import subprocess
import random
random_min = random.randrange(1,59)

print('''
Welcome to the add https to a web service script using nginx
Here is the scenario:
  You have a webservice you would like to use a virtual host to
  proxy port 80 traffic to your webservice.  But now you want
  to use https and a lets encrypt cert, this script does that.
  It redirects http traffic to https, applies for a lets encrypt
  cert, and forwards port 443 traffic to the port you specify.

All you need to provide is the domain name, port, and IP address.

''')
domain_name = raw_input('Please enter the domain name: ')
port = raw_input('Please enter the port [1024-9999]: ')
ip_address = raw_input('Please enter the IP address: ')
print(' ')

nginx_config_raw = '''
map $http_upgrade $connection_upgrade {{
  default upgrade;
  ''      close;
}}

upstream websocket{1} {{
  server 127.0.0.1:{1};
}}

server {{
  listen {2}:443 ssl;
  server_name {0};
  ssl_certificate     /etc/letsencrypt/live/{0}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/{0}/privkey.pem;
  
  location / {{
    proxy_pass http://websocket{1};
    proxy_read_timeout 600;
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_set_header   Host             $host;
    proxy_set_header   X-Real-IP        $remote_addr;
    proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
    proxy_set_header   Upgrade          $http_upgrade;
    proxy_set_header   Connection       "upgrade";
    if ($request_method = 'OPTIONS') {{
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        #
        # Custom headers and headers various browsers *should* be OK with but aren't
        #
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        #
        # Tell client that this pre-flight info is valid for 20 days
        #
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain charset=UTF-8';
        add_header 'Content-Length' 0;
        return 204;
     }}
     if ($request_method = 'POST') {{
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Expose-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
     }}
     if ($request_method = 'GET') {{
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Expose-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
     }}
  }}
}}

server {{
    listen {2}:80;
    server_name {0};
    return 301 https://{0}$request_uri;
}}
'''
nginx_config = nginx_config_raw.format(domain_name, port, ip_address)
nginx_config_available = '/etc/nginx/sites-available/'+domain_name

def write_nginx_config():
  f = open(nginx_config_available, 'w')
  f.write(nginx_config)
  print('Writing nginx config')
  f.close()

  os.symlink(nginx_config_available, '/etc/nginx/sites-enabled/' + domain_name)
  print('Adding symlink from sites-available to sites-enabled')

if (os.path.isfile(nginx_config_available)):
  answer = raw_input('nginx config for site exists, overwrite? [Y/n]')
  if (answer.lower() == 'y'):
    write_nginx_config()
else:
  write_nginx_config()


# download let's encrypt
print('Downloading lets encrypt')
subprocess.check_call('wget https://dl.eff.org/certbot-auto', shell=True)
subprocess.check_call('chmod a+x certbot-auto', shell=True)
subprocess.check_call('cp certbot-auto /opt', shell=True)

# shut down nginx
print('Attempting to shut down nginx')
try:
  systemd_check = subprocess.check_call('systemctl stop nginx', shell=True)
except:
  systemd_check = 1
  print("systemd didn't work")
if (systemd_check != 0):
  try:
    service_check = subprocess.check_call('service nginx stop', shell=True)
  except:
    service_check = 1
    print("service didn't work")
if (systemd_check != 0 and service_check != 0):
  try:
    initd_check = subprocess.check_call('/etc/init.d/nginx stop', shell=True)
  except:
    initd_check = 1
    print("initd didn't work")
if (systemd_check != 0 and service_check != 0 and initd_check != 0):
  print('Could not stop nginx, giving up')
  sys.exit(1)

# apply for cert
print('Appling for lets encrypt cert')
subprocess.check_call('./certbot-auto certonly --standalone -d '+domain_name, shell=True)

# start nginx
print('Attempting to restart nginx')
if (systemd_check == 0):
  subprocess.check_call('systemctl start nginx', shell=True)
elif (service_check == 0):
  subprocess.check_call('service nginx start', shell=True)
elif (initd_check == 0):
  subprocess.check_call('/etc/init.d/nginx start', shell=True)
else:
  print("couldn't restart nginx")
  sys.exit(1)

# print renew script and crontab additions
print('''
  To renew this cert you should make a script that contains something like this:

#!/bin/bash
systemctl stop nginx # or equivalent
/opt/certbot-auto certonly --standalone -d {0}
systemctl start nginx # or equivalent

  You could then save it to

/opt/renew-{0}-cert.sh

  And then add this to your crontab

{1} 0 1 * * /opt/renew-{0}-cert.sh

  With the command

crontab -e

  To renew your lets encrypt cert once a month
'''.format(domain_name, random_min))
