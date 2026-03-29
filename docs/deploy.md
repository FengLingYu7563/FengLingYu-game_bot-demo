# Oracle Cloud VM Deployment Guide

Oracle Cloud offers an Always Free tier, which includes:

- 2 AMD Compute VMs
- Up to 4 ARM Ampere A1 OCPUs and 24GB RAM — 3,000 OCPU hours and 18,000 GB hours **per month**

This makes it a great free option for hosting a Discord bot or any other lightweight application.
> **Tip:** Upgrading to a paid account increases your chances of claiming Always Free ARM instances, as they are in high demand.
> As long as you stay within the free tier limits, you won't be charged.

When signing up, choose your region carefully — **it cannot be changed later**.

***Avoid Japan East (Tokyo)*** and ***South Korea Central (Seoul)*** as they tend to have limited resource availability. ***Singapore*** and ***Japan Central (Osaka)*** are better alternatives.

---

## Create a VM Instance

Go to **Compute → Instances → Create Instance**, select the **Ampere A1** shape, and generate an SSH key pair.

**Make sure to save both the public and private keys** — you will need the private key to connect to your VM.

![picture1](https://github.com/user-attachments/assets/53422079-a952-495b-a0b8-aaf547bb79f8)

![picture2](https://github.com/user-attachments/assets/29055868-81a2-47ea-ba29-e32af55c1a34)

---

## SSH
```bash
ssh -i <PRIVATE_KEY_PATH> opc@<YOUR_VM_IP>
```

---

## Setup
```bash

sudo dnf update -y

git clone <YOUR_REPO_URL>
cd <YOUR_REPO_NAME>
pip3 install -r requirements.txt
nano .env
```
> Press Ctrl+X → Y → Enter to save and exit.
> Press Ctrl+B → [ to enter scroll mode, use arrow keys to scroll, and press Q to exit.

---

## Run with tmux
### start a session
```bash
tmux new -s bot
python3.11 main.py
```
> Press Ctrl+B → D to leave and keeps running in background.

---

## Maintenance
```bash
tmux attach -t bot

# Ctrl + C to stop the running process

# pull the latest change
git pull

python3.11 main.py
```
