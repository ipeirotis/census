#!/bin/bash

docker build -t ipeirotis/census .

docker push ipeirotis/census

python3 restart_vm.py

curl http://census.ipeirotis.com:5000/details_tract_level/?address=3%20Washington%20Square%20Village,%20New%20York%20NY

