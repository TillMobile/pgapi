#!/usr/bin/env bash

# Clean up env
cd /opt/
rm -rf venv
rm .env

# Setup Environment
DC_DATABASE=till`cat /dev/urandom | tr -cd 'a-f0-9' | head -c 32`
DC_USER=till`cat /dev/urandom | tr -cd 'a-f0-9' | head -c 32`
DC_PASSWORD=till`cat /dev/urandom | tr -cd 'a-f0-9' | head -c 32`

sudo touch /opt/.env
sudo chmod 777 /opt/.env
printf "export DB_DATABASE='${DC_DATABASE}'\n" >> /opt/.env
printf "export DB_SCHEMA='public'\n" >> /opt/.env
printf "export DB_USER='${DC_USER}'\n" >> /opt/.env
printf "export DB_PASSWORD='${DC_PASSWORD}'\n" >> /opt/.env
printf "export DB_HOST='127.0.0.1'\n" >> /opt/.env
printf "export DB_PORT=5432\n" >> /opt/.env
printf "export DB_CONNECTION_POOL_MIN=5\n" >> /opt/.env
printf "export DB_CONNECTION_POOL_MAX=25\n" >> /opt/.env
printf "export API_DEFAULT_COLLECTION_ROW_LIMIT=25\n" >> /opt/.env

# Setup DB as
sudo service postgresql start
. /opt/.env
sudo -u postgres psql -c "create user ${DC_USER} with password '${DC_PASSWORD}';"
sudo -u postgres psql -c "alter user ${DC_USER} with superuser;"
sudo -u postgres psql -c "ALTER USER ${DC_USER} CREATEDB;"
sudo -u postgres psql -c "alter user postgres with password '${DC_PASSWORD}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '${DC_DATABASE}'" | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE ${DC_DATABASE}"
sudo -u postgres psql -c "ALTER DATABASE ${DC_DATABASE} OWNER to ${DC_USER};"

# Setup Application Environment
cd /opt/
virtualenv venv