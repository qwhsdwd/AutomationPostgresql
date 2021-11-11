# 安装 expect
apt install expect

# 安装最高版本的postgresql
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get install postgresql

# 升级pip3
pip3 install --upgrade setuptools -i https://pypi.douban.com/simple
pip3 install --upgrade pip -i https://pypi.douban.com/simple
# 安装psycopg2依赖包
pip3 install psycopg2==2.7.3.2 -i https://pypi.douban.com/simple
