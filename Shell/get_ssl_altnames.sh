#! /bin/sh

if [ -z $1 ]
then
  echo "No argument given. Waiting a DNS name or an IP"
  exit 1;
fi

for N in $(openssl s_client -connect $1:443 </dev/null 2>&1 | openssl x509 -text|grep -A1 "X509v3 Subject Alternative Name"|tail -1|sed 's/[DNS:|,]//g')
do
  echo "=== $N ==="
  dig +short $N
done
