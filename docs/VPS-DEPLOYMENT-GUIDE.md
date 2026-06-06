# Hostinger VPS Deployment Guide

This guide moves the complete CRS lab from your Mac to an Ubuntu VPS.

The Mac becomes your control workstation:

```text
VS Code -> Git commit -> GitHub push
```

The VPS becomes your runtime:

```text
GitHub pull -> Docker build -> Containers -> Prometheus -> Grafana
```

## Target Architecture

```text
Mac / VS Code
    |
    | git push
    v
GitHub repository
    |
    | git pull
    v
Hostinger Ubuntu VPS
    |
    |-- Reservation Service
    |-- Notification Worker
    |-- Mock PMS
    |-- PostgreSQL
    |-- Redis
    |-- Prometheus
    |-- Grafana
```

PostgreSQL, Redis, APIs, Prometheus, and Grafana bind only to VPS localhost. You access them through an encrypted SSH tunnel.

## 1. Inspect The VPS

Run on the VPS:

```bash
whoami
hostname
cat /etc/os-release
uname -m
free -h
df -h
nproc
```

Recommended minimum for the complete lab:

- 2 CPU cores
- 4 GB RAM
- 20 GB free disk

With 2 GB RAM, run the app without Prometheus and Grafana or add swap.

## 2. Update Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates
```

Reboot if the operating system installed a kernel update:

```bash
sudo reboot
```

Reconnect after the VPS returns:

```bash
ssh <user>@<vps-ip>
```

## 3. Check Docker

Hostinger may already have Docker installed.

```bash
docker --version
docker compose version
sudo systemctl status docker --no-pager
```

If both Docker commands work, skip to section 5.

## 4. Install Docker On Ubuntu

Use Docker's official Ubuntu repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Add the repository:

```bash
echo \
  "Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc" \
  | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null
```

Install Docker:

```bash
sudo apt update
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

Enable it:

```bash
sudo systemctl enable --now docker
sudo docker run --rm hello-world
```

Allow your login user to run Docker:

```bash
sudo usermod -aG docker "$USER"
```

Log out and reconnect so the group change takes effect:

```bash
exit
```

Then reconnect and verify:

```bash
docker version
docker compose version
```

## 5. Configure Git On The VPS

Set your identity:

```bash
git config --global user.name "Sanjay Devang"
git config --global user.email "YOUR_GITHUB_EMAIL"
git config --global init.defaultBranch main
```

Check:

```bash
git config --global --list
```

Git identity is used only when you make commits from the VPS. Normally, make code changes on the Mac and use the VPS only to pull and deploy.

## 6. Clone The GitHub Repository

Create an application directory:

```bash
sudo mkdir -p /opt/apps
sudo chown "$USER":"$USER" /opt/apps
cd /opt/apps
```

Clone:

```bash
git clone https://github.com/sanjaydevang/SRE-SETUP.git
cd SRE-SETUP
```

Verify:

```bash
git remote -v
git branch --show-current
git log --oneline -5
```

If the repository is private, use an SSH deploy key or a GitHub personal access token. Do not save a token inside scripts or the repository.

## 7. Create VPS Secrets

Create `.env` from the example:

```bash
cp .env.example .env
```

Generate two passwords:

```bash
openssl rand -base64 32
openssl rand -base64 32
```

Edit:

```bash
nano .env
```

Set:

```dotenv
POSTGRES_PASSWORD=first-generated-password
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=second-generated-password
```

Protect the file:

```bash
chmod 600 .env
```

The `.env` file is excluded by `.gitignore`. Never commit it.

## 8. Validate Configuration

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  config >/dev/null
```

If the command returns without an error, the merged Compose configuration is valid.

## 9. Start The Complete Lab

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  up -d --build
```

The first build takes longer because Docker downloads images and installs Python dependencies.

Check containers:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps
```

Watch startup logs:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  logs -f --tail=100
```

Use `Ctrl+C` to stop following logs. It does not stop containers.

## 10. Verify The Deployment

Run:

```bash
./scripts/vps-health-check.sh
```

Run the application smoke test on the VPS:

```bash
./scripts/smoke-test.sh
```

Check specific logs:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  logs --tail=100 reservation-service notification-worker mock-pms prometheus grafana
```

## 11. Access The Lab From Your Mac

Keep the services private and create an SSH tunnel from a Mac terminal:

```bash
ssh \
  -L 8000:127.0.0.1:8000 \
  -L 8100:127.0.0.1:8100 \
  -L 9000:127.0.0.1:9000 \
  -L 9090:127.0.0.1:9090 \
  -L 9093:127.0.0.1:9093 \
  -L 3000:127.0.0.1:3000 \
  -L 8080:127.0.0.1:8080 \
  -L 9080:127.0.0.1:9080 \
  <user>@<vps-ip>
```

Keep that terminal open.

Then open on the Mac:

- API documentation: <http://localhost:8000/docs>
- Worker metrics: <http://localhost:8100/metrics>
- Mock PMS: <http://localhost:9000/docs>
- Prometheus: <http://localhost:9090>
- Alertmanager: <http://localhost:9093>
- Grafana: <http://localhost:3000>
- cAdvisor: <http://localhost:8080>

Grafana uses the username and password from the VPS `.env`.

## 12. Hostinger Firewall

Because application ports bind to `127.0.0.1`, they are not directly exposed publicly.

In the Hostinger firewall, allow:

```text
TCP 22 from your IP address
```

Do not expose these directly:

```text
5432 PostgreSQL
6379 Redis
9090 Prometheus
3000 Grafana
```

If your home IP changes frequently, temporarily allow SSH more broadly, then tighten it after confirming access. Never close your current SSH session until a second session successfully connects with the new rule.

## 13. Normal Development And Deployment Workflow

On the Mac:

```bash
git checkout -b feature/my-change
```

Make changes, then:

```bash
git status
git add <files>
git commit -m "Describe the change"
git push -u origin feature/my-change
```

After review and merge to `main`, deploy from the VPS:

```bash
cd /opt/apps/SRE-SETUP
./scripts/vps-deploy.sh
./scripts/vps-health-check.sh
```

The deployment script performs:

```text
git pull --ff-only
docker compose up -d --build
docker compose ps
```

This is manual continuous delivery. Later, GitHub Actions can automate the VPS deployment after CI tests pass.

## 14. Daily Operations

Status:

```bash
cd /opt/apps/SRE-SETUP
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  ps
```

Resource usage:

```bash
docker stats
free -h
df -h
uptime
```

Recent logs:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  logs --since=30m
```

Restart one service:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  restart notification-worker
```

Restart all:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  restart
```

## 15. Stop And Start

Stop containers but keep them:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  stop
```

Start stopped containers:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  start
```

Remove containers but preserve named volumes:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  down
```

Do not add `-v` unless you intentionally want to delete PostgreSQL, Prometheus, and Grafana data.

## 16. Reboot Recovery

Docker is enabled at boot:

```bash
systemctl is-enabled docker
```

Containers use:

```text
restart: unless-stopped
```

Therefore, they should return after a VPS reboot.

Test during a learning window:

```bash
sudo reboot
```

Reconnect and verify:

```bash
cd /opt/apps/SRE-SETUP
./scripts/vps-health-check.sh
```

## 17. If The VPS Is Low On Memory

Check:

```bash
free -h
docker stats --no-stream
```

Run only the application:

```bash
docker compose up -d --build
```

Stop observability containers:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.observability.yml \
  stop prometheus grafana
```

Do not run Docker Compose and Kubernetes versions of the lab simultaneously on a small VPS.

## 18. Backups

Before major changes:

- create a Hostinger VPS snapshot
- verify the GitHub repository is current
- back up important database data

Simple PostgreSQL backup:

```bash
mkdir -p backups
docker compose exec -T postgres \
  pg_dump -U crs -d crs > "backups/crs-$(date +%F-%H%M).sql"
```

List:

```bash
ls -lh backups
```

## 19. Troubleshooting

Container exited:

```bash
docker compose ps -a
docker compose logs --tail=200 <service>
```

Port already used:

```bash
sudo ss -lntp
```

Disk full:

```bash
df -h
docker system df
```

Memory pressure:

```bash
free -h
docker stats --no-stream
dmesg | grep -i -E "oom|killed process"
```

Prometheus target missing:

```text
Open http://localhost:9090/targets through the SSH tunnel.
```

Check Prometheus logs:

```bash
docker compose logs --tail=200 prometheus
```

## 20. Enterprise Experience You Gain

This VPS lab gives practical experience with:

- Linux server administration
- SSH access
- Git-based deployments
- Docker image builds
- Compose service orchestration
- secret handling
- network exposure decisions
- health checks
- log investigation
- Prometheus/Grafana operations
- alert testing
- restart and recovery
- backups and resource monitoring

It is production-like experience, but one VPS is not the same as:

- multi-node Kubernetes
- high availability
- multi-AZ architecture
- managed load balancers
- cluster autoscaling
- enterprise IAM

After this Compose deployment is stable, the next phase is K3s or a managed Kubernetes cluster. Do not run both versions simultaneously until VPS capacity is confirmed.
