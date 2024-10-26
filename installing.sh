journalctl --vacuum-size=500M;
apt update -y;
apt install postgresql postgresql-contrib -y;
apt install python3.11 -y;
#apt install pip -y;
apt install libpq-dev -y;

pip install -r requirements.txt;
systemctl enable postgresql.service; service postgresql start;
sudo -u postgres psql -c "CREATE ROLE bot LOGIN PASSWORD 'Monet_Bot_123';";
sudo -u postgres psql -c "CREATE DATABASE bot_db WITH OWNER = bot;";
cp bot.service /etc/systemd/system;
systemctl daemon-reload;
systemctl enable bot.service;
systemctl start bot;