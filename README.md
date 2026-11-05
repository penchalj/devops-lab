# DevOps Interview Lab (Docker + Jenkins + Linux VM + Ansible)

Hands-on lab for the RATIONAL work trial. Setup takes about 1.5–2 hours. After that, use `DRILLS.md`.

```
devops-lab/
├── docker-compose.yml     Jenkins controller + SSH build agent (network: lab-net)
├── jenkins/               Jenkins image with Docker CLI and plugins
├── app/                   Small Python web service, Dockerfile, unit tests, Jenkinsfile
├── vm/cloud-init.yaml     Ubuntu VM definition (Multipass)
├── ansible/               Playbook: app as a systemd service behind nginx + TLS
└── DRILLS.md              Break-and-fix exercises
```

**Hardware:** 16 GB RAM is comfortable (8 GB works if you stop Jenkins while using the VM).

---

## 0. Install the tools

**Windows (recommended path)**
1. Enable WSL2 and install Ubuntu: `wsl --install -d Ubuntu-24.04` (PowerShell as admin, then reboot).
2. Install **Docker Desktop**. Under Settings → Resources → WSL integration, enable Ubuntu.
3. Install **Multipass** from https://canonical.com/multipass. It needs Hyper-V (Windows Pro) or VirtualBox (Windows Home).
4. In WSL Ubuntu: `sudo apt update && sudo apt install -y ansible git`

> Do all your work **inside WSL, in your Linux home** (`~/devops-lab`), not under `/mnt/c/...`.
> Ansible ignores `ansible.cfg` in world-writable directories, and `/mnt/c` is world-writable.

**Linux / macOS:** install Docker Engine/Desktop, Multipass (`sudo snap install multipass` / `brew install multipass`), and Ansible.

Check:
```bash
docker version && docker compose version && multipass version && ansible --version
```

---

## 1. Start Jenkins

```bash
cd ~/devops-lab
docker compose up -d --build jenkins
docker compose logs -f jenkins          # wait for "Jenkins is fully up and running", then Ctrl+C
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

1. Open http://localhost:8080 and paste the password.
2. Choose **Select plugins to install** → **None** (the needed plugins are already in the image), then create an admin user.
3. Check that Docker works from Jenkins: `docker compose exec jenkins docker ps`

---

## 2. Add the SSH build agent

```bash
mkdir -p keys
ssh-keygen -t ed25519 -f keys/jenkins_agent -N "" -C jenkins-agent
echo "JENKINS_AGENT_SSH_PUBKEY=$(cat keys/jenkins_agent.pub)" > .env
docker compose up -d agent
```

In Jenkins:
1. **Manage Jenkins → Credentials → System → Global → Add credentials**
   - Kind: *SSH Username with private key*. ID: `agent-ssh`. Username: `jenkins`
   - Private key: *Enter directly*. Paste the content of `keys/jenkins_agent`.
2. **Manage Jenkins → Nodes → New node** `linux-agent-1` (Permanent Agent)
   - Remote root directory: `/home/jenkins/agent`. Labels: `linux`. Executors: `2`
   - Launch method: *Launch agents via SSH*. Host: `jenkins-agent`. Credentials: `agent-ssh`
   - Host key verification: *Non verifying* (lab only)
3. Save. The agent should come online within a few seconds. If not, open its **Log**.

---

## 3. Run the pipeline

Jenkins checks out code from Git, so push this folder to a repository first, for example a private GitHub repo:

```bash
cd ~/devops-lab
printf "keys/\n.env\n" > .gitignore
git init && git add . && git commit -m "DevOps lab"
git branch -M main
git remote add origin git@github.com:<your-user>/devops-lab.git
git push -u origin main
```

> For a private repo, add a credential in Jenkins (a GitHub username + personal access token works) and select it in the job.

In Jenkins: **New Item → `lab-app` → Pipeline**
- Definition: *Pipeline script from SCM*. SCM: Git. Repository URL: your repo. Branch: `*/main`
- Script Path: `app/Jenkinsfile`

Click **Build Now**. The first run may show no parameters; from the second run, use **Build with Parameters** and tick `RUN_ON_AGENT` to also test the SSH agent.

What the pipeline does: unit tests in a `python:3.12-slim` container → `docker build` → runs the container on `lab-net` and checks `/health` with curl → cleans up in `post { always }`.

---

## 4. Create the Linux VM

```bash
ssh-keygen -t ed25519 -f ~/.ssh/lab_vm -N "" -C lab-vm
cat ~/.ssh/lab_vm.pub                    # paste this into vm/cloud-init.yaml (replace REPLACE_WITH_YOUR_PUBLIC_KEY)

multipass launch 24.04 --name lab-vm --cpus 2 --memory 2G --disk 15G --cloud-init vm/cloud-init.yaml
multipass info lab-vm                    # note the IPv4 address
ssh -i ~/.ssh/lab_vm labadmin@<VM_IP>
```

> **Windows:** if `multipass` only works in PowerShell, launch the VM there, using the cloud-init file path on Windows. Then use `ssh` and Ansible from WSL. If WSL cannot reach the VM IP, run `ssh` from PowerShell and use the fallback in step 5.

Useful commands: `multipass list`, `multipass shell lab-vm`, `multipass stop|start lab-vm`, `multipass delete --purge lab-vm` (rebuild from scratch).

---

## 5. Configure the VM with Ansible

```bash
cd ~/devops-lab/ansible
sed -i "s/REPLACE_WITH_VM_IP/<VM_IP>/" inventory.ini
ansible labvm -m ping                    # expect "pong"
ansible-playbook site.yml --check --diff # dry run
ansible-playbook site.yml
ansible-playbook site.yml                # second run: expect changed=0 (idempotent)
curl -k https://<VM_IP>/health
```

**Fallback if WSL cannot reach the VM:** copy the repo into the VM, then run Ansible there against `localhost` using `ansible_connection=local`.

Result: `labapp.service` listens on 127.0.0.1:8000, and nginx redirects port 80 to 443 and proxies to the app over TLS (self-signed).

---

## 6. Practise

Work through `DRILLS.md`. Talk out loud while you diagnose, as you will on Monday.

## Cleanup

```bash
docker compose down            # keep Jenkins data
docker compose down -v         # delete Jenkins data as well
multipass delete --purge lab-vm
```

## Talking points this lab gives you

- Why the controller runs no builds in production, and how agents are labelled and connected (SSH vs inbound/JNLP vs Kubernetes pods).
- The trade-offs of mounting the Docker socket: it is effectively root on the host. Alternatives are DinD, rootless Docker, Kaniko/Buildah, and ephemeral agents.
- Pipeline hygiene: timeouts, build discarders, `post { always }` cleanup, a smoke test before promoting an image, and image tags tied to the build number or git SHA.
- Idempotent configuration with Ansible: `creates:`, handlers, `--check --diff`.
- The app binds to localhost and nginx terminates TLS: the reverse proxy is the only public entry point.
