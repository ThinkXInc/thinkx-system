# ⭐️ Transcript Scraper Machine Setup

_created: 20231028T182604Z / updated: 20231106T010613Z_

```
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libbz2-dev liblzma-dev -y
```

```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

```
wget https://www.python.org/ftp/python/3.9.6/Python-3.9.6.tgz
tar -xf Python-3.9.6.tgz
cd Python-3.9.6/
./configure --enable-optimizations
make -j 30
sudo make altinstall
cd ..
sudo ln -s /usr/local/bin/python3.9 /usr/local/bin/python
python3.9 --version
```

```
sudo apt-get install -y supervisor
```

```
sudo apt-get install unzip -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm awscliv2.zip
rm -rf aws/
```

```
curl -O https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/118.0.5993.70/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

```
python3.9 -m venv /home/ubuntu/transcript-scraper/venv
source /home/ubuntu/transcript-scraper/venv/bin/activate
pip install -r /home/ubuntu/transcript-scraper/requirements.txt
```

```
nohup supervisord -c /home/ubuntu/transcript-scraper/supervisor/urls_worker.conf
```
