# Logging in
```bash
#Amazon Linux 2023: 
ssh -i <KEY.pem> ec2-user@<EC2_IP>
```

# Installation
1) Install system deps

```bash
# Amazon Linux 2023 (currently used)
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip certbot
# Ubuntu
# sudo apt update
# sudo apt install -y python3 python3-pip python3-venv certbot
```

2) Set up a project and venv
```bash
mkdir -p ~/nanda-agent && cd ~/nanda-agent
# Amazon Linux:
python3.11 -m venv .venv && source .venv/bin/activate

# Ubuntu:
# python3 -m venv .venv && source .venv/bin/activate
```

3) Install Python packages
```bash
pip install --upgrade pip
pip install nanda-adapter crewai langchain-anthropic
```

4) Configure your Domain and SSL Certificates

```bash
cd nanda_agent/examples

sudo certbot certonly --standalone -d ai-studio-hw2.ostrovskiy.xyz
sudo cp -L /etc/letsencrypt/live/ai-studio-hw2.ostrovskiy.xyz/fullchain.pem .
sudo cp -L /etc/letsencrypt/live/ai-studio-hw2.ostrovskiy.xyz/privkey.pem .
sudo chown $USER:$USER fullchain.pem privkey.pem
chmod 600 fullchain.pem privkey.pem
```



5) Set Your enviroment variables ANTHROPIC_API_KEY
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export DOMAIN_NAME="<YOUR_DOMAIN_NAME.COM>"
```

# Run an example agent __(langchain_pirate.py)__
```bash
nohup python3 langchain_pirate.py > out.log 2>&1 &
```

# Get  enrollment link from log file
```bash
cat out.log
```