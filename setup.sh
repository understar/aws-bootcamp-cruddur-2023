#! /usr/bin/bash

# Check if psql exists and install if not found
if ! command -v "psql" &> /dev/null; then
    echo "psql not found. Installing..."
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
    echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
    sudo apt update
    sudo apt install -y postgresql-client-13 libpq-dev
fi

export CODESPACE_IP=$(curl ifconfig.me)
source "$CODESPACE_VSCODE_FOLDER/backend-flask/bin/rds-update-sg-rule"

cd $CODESPACE_VSCODE_FOLDER/backend-flask
pip install -r requirements.txt

cd $CODESPACE_VSCODE_FOLDER/frontend-react-js
npm i

exit 0