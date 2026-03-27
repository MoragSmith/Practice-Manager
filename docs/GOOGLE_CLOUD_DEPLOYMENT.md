# Practice Manager: Google Cloud Deployment Guide

This guide walks you through hosting the Practice Manager web app on Google Cloud, with your OTPD Scores library on Google Drive.

---

## The Data Challenge

Your OTPD Scores library lives on **Google Drive**. The web app needs to:

- Read the library structure (sets, tunes, parts)
- Read/write `practice_status.json`
- Stream PDFs and WAVs on demand

**Two approaches:**

| Approach | Pros | Cons |
|----------|------|------|
| **VM + rclone mount** | Simple, app uses filesystem as-is | VM runs 24/7 (or you start it when needed); small monthly cost |
| **Cloud Run + Drive API** | Serverless, pay per request | Requires code changes to fetch files via API; more setup |

**Recommended:** Start with **Compute Engine VM + rclone**. It’s the fastest path and needs no code changes. You can move to Cloud Run + Drive API later if you want.

---

## Prerequisites

1. **Google Cloud account** – [console.cloud.google.com](https://console.cloud.google.com)
2. **Billing enabled** – Free tier covers a small VM; you’ll need a billing account
3. **OTPD Scores in Google Drive** – Your library in a Drive folder (personal or shared)

---

## Part 1: Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown (top left) → **New Project**
3. Name it (e.g. `practice-manager`) → **Create**
4. Select the new project

---

## Part 2: Enable APIs and Create a VM

### 2.1 Enable Compute Engine

1. **Navigation menu** (☰) → **APIs & Services** → **Library**
2. Search for **Compute Engine API** → **Enable**

### 2.2 Create a VM Instance

1. **Navigation menu** → **Compute Engine** → **VM instances**
2. **Create Instance**
3. Suggested settings:
   - **Name:** `practice-manager`
   - **Region:** Choose one near you (e.g. `us-central1`)
   - **Machine type:** `e2-micro` (free tier) or `e2-small` for more headroom
   - **Boot disk:** Ubuntu 22.04 LTS, 10 GB
   - **Firewall:** Allow HTTP and HTTPS traffic
4. **Create**

### 2.3 Connect to the VM

1. In the VM list, click **SSH** next to your instance
2. A browser SSH window opens

---

## Part 3: Set Up Google Drive Access (rclone)

rclone lets the VM access your Google Drive as a local folder.

### 3.1 Install rclone

In the SSH terminal:

```bash
curl https://rclone.org/install.sh | sudo bash
```

### 3.2 Configure rclone for Google Drive

```bash
rclone config
```

1. **n** (new remote)
2. **Name:** `gdrive`
3. **Storage:** `drive` (Google Drive)
4. **client_id / client_secret:** press Enter (use defaults)
5. **scope:** `1` (Full access)
6. **root_folder_id:** Enter
7. **service_account_file:** Enter
8. **Edit advanced config?** `n`
9. **Use auto config?** `n` (we’re on a headless VM)

You’ll see a URL. Copy it.

### 3.3 Authorize from Your Mac

1. On your Mac, open that URL in a browser
2. Sign in with the Google account that has OTPD Scores
3. Allow access
4. Copy the verification code
5. Paste it into the SSH terminal
6. **y** to confirm
7. **q** to quit config

### 3.4 Test the Connection

```bash
rclone lsd gdrive:
```

You should see your Drive top-level folders. Find the folder that contains OTPD Scores (e.g. `My Drive` or a shared drive name).

### 3.5 Create a Mount Point

```bash
sudo mkdir -p /mnt/otpd-scores
sudo chown $USER:$USER /mnt/otpd-scores
```

### 3.6 Mount Google Drive

Replace `gdrive:Path/To/OTPD Scores` with your actual path. Examples:

- `gdrive:OTPD Scores` (folder in My Drive)
- `gdrive:Shared drives/SharedDriveName/OTPD Scores` (shared drive)

```bash
rclone mount gdrive:"OTPD Scores" /mnt/otpd-scores --vfs-cache-mode full --dir-cache-time 72h --daemon
```

Check it:

```bash
ls /mnt/otpd-scores
```

You should see Section folders, `#Script Resources`, etc.

### 3.7 Make the Mount Persistent (Optional)

To remount after reboot, add a systemd service or a startup script. For now, if the VM restarts, run the `rclone mount` command again.

---

## Part 4: Deploy the Practice Manager App

### 4.1 Install Python and Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### 4.2 Clone Your Repo (or Upload)

**Option A – From GitHub:**

```bash
cd ~
git clone https://github.com/MoragSmith/Practice-Manager.git
cd Practice-Manager
```

**Option B – Upload from your Mac:**

From your Mac (in Terminal):

```bash
gcloud compute scp --recurse /path/to/Practice\ Manager/* practice-manager:~/Practice-Manager/ --zone=YOUR_ZONE
```

Replace `YOUR_ZONE` with your VM’s zone (e.g. `us-central1-c`).

### 4.3 Create a Virtual Environment

On an **e2-micro** VM (1 GB RAM), use the minimal web-only requirements to avoid out-of-memory during install:

```bash
cd ~/Practice-Manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-web-only.txt
```

On larger VMs, you can use the full requirements:

```bash
pip install -r requirements.txt -r requirements-web.txt
```

### 4.4 Set the Library Path

The app must use the mounted Drive path:

```bash
export LIBRARY_ROOT=/mnt/otpd-scores
```

### 4.5 Test the App

```bash
uvicorn src.practice_manager.web.main:app --host 0.0.0.0 --port 8000
```

In another SSH session (or from your Mac), test:

```bash
curl http://EXTERNAL_IP:8000/
```

Replace `EXTERNAL_IP` with the VM’s external IP (from the Compute Engine console).

### 4.6 Run as a Service (Always On)

Create a systemd service so the app starts on boot and restarts on failure:

```bash
sudo nano /etc/systemd/system/practice-manager.service
```

Paste (adjust paths if needed):

```ini
[Unit]
Description=Practice Manager Web
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Practice-Manager
Environment="LIBRARY_ROOT=/mnt/otpd-scores"
Environment="PATH=/home/YOUR_USERNAME/Practice-Manager/venv/bin"
ExecStart=/home/YOUR_USERNAME/Practice-Manager/venv/bin/uvicorn src.practice_manager.web.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Replace `YOUR_USERNAME` with your Linux username (run `whoami` to check).

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable practice-manager
sudo systemctl start practice-manager
sudo systemctl status practice-manager
```

---

## Part 5: Expose the App via HTTPS (Optional but Recommended)

### 5.1 Reserve a Static IP

1. **Compute Engine** → **VPC network** → **IP addresses**
2. **Reserve external static address**
3. Name it, attach to your VM

### 5.2 Point a Domain (Optional)

If you have a domain, add an A record to the static IP.

### 5.3 Use a Load Balancer or Reverse Proxy

For HTTPS with a certificate, use either:

- **Google Cloud Load Balancer** (more setup, automatic HTTPS)
- **Caddy or nginx** on the VM as a reverse proxy (simpler)

**Simple Caddy example** (install Caddy, then):

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

Configure Caddy to proxy to `localhost:8000` and handle HTTPS. (I can provide a full Caddyfile if you want.)

---

## Part 6: Password Protection

Practice Manager supports HTTP Basic Authentication. Set these environment variables before starting the app:

```bash
export AUTH_USERNAME="your_username"
export AUTH_PASSWORD="your_password"
LIBRARY_ROOT=/mnt/otpd-scores python -m uvicorn src.practice_manager.web.main:app --host 0.0.0.0 --port 8000
```

The browser will prompt for username and password on first visit. If `AUTH_USERNAME` and `AUTH_PASSWORD` are not set, the site is open (no auth).

For the systemd service, add to the `[Service]` section:
```ini
Environment="AUTH_USERNAME=your_username"
Environment="AUTH_PASSWORD=your_password"
```

## Part 7: Additional Security (Optional)

For stronger protection:

1. **Google OAuth** – Sign in with your Google account
2. **IAP** – Identity-Aware Proxy so only your Google account can reach the VM
3. **VPN** – Restrict access to your network

---

## Quick Reference

**Zone for this deployment:** `us-central1-c`

| Step | Command / Action |
|------|------------------|
| Upload from Mac | `gcloud compute scp Practice-Manager-full.zip moragsmith@instance-20260221-213425:~ --zone=us-central1-c` |
| Mount Drive | `rclone mount gdrive:"OTPD Scores" /mnt/otpd-scores --vfs-cache-mode full --daemon` |
| Run app (foreground) | `LIBRARY_ROOT=/mnt/otpd-scores python -m uvicorn src.practice_manager.web.main:app --host 0.0.0.0 --port 8000` |
| Run app (background, survives SSH close) | `bash ~/Practice-Manager/deploy/start-app.sh` |
| Check service | `sudo systemctl status practice-manager` |
| View logs | `sudo journalctl -u practice-manager -f` |

---

## Troubleshooting

**"Could not discover OTPD Scores library"**  
- Ensure `LIBRARY_ROOT=/mnt/otpd-scores` is set  
- Check the mount: `ls /mnt/otpd-scores`  
- Remount if needed: `rclone mount ...`

**rclone mount drops**  
- Use `--vfs-cache-mode full`  
- Consider `rclone sync` on a schedule instead of mount (copy to local disk, app reads local)

**Slow PDF/WAV loading**  
- Drive API has latency; `--vfs-cache-mode full` helps  
- For heavy use, sync to local SSD and point `LIBRARY_ROOT` there

---

## Cost Estimate (Rough)

- **e2-micro VM:** Free tier (1 per account) or ~$6/month
- **e2-small:** ~$12/month
- **10 GB disk:** ~$0.40/month
- **Traffic:** First 1 GB free, then ~$0.12/GB

Total for light use: **~$0–10/month** depending on VM size and traffic.
