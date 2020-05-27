# This will create diffie hellman group
openssl dhparam -dsaparam -out dhparam.pem 4096

# This will create the self-signed certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx-selfsigned.key -out nginx-selfsigned.crt