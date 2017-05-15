# lets-nginx-proxy
Set up nginx, apply for a lets encrypt cert, automated

Welcome to the add https to a web service script using nginx
Here is the scenario:

You have a webservice you would like to use a virtual host to
proxy port 80 traffic to your webservice.  But now you want
to use https and a lets encrypt cert, this script does that.
It redirects http traffic to https, applies for a lets encrypt
cert, and forwards port 443 traffic to the port you specify. 

All you need to provide is the domain name, port, and IP address.

```
Please enter the domain name: example.com
Please enter the port [1024-9999]: 2345
Please enter the IP address: 123.456.789.012
```

In addtion this script forwards websockets and enables CORS.
