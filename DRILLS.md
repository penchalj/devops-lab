# Break-and-fix drills

How to use these: inject the fault (ideally have someone else do it, or do it and wait a day), then diagnose it **out loud**:
symptom → hypothesis → command to check → fix → how to prevent it next time.
Each drill has a few hints at the end; try without them first.

---

## A. Jenkins / CI

| # | Inject the fault | Expected symptom |
|---|---|---|
| A1 | In `test_app.py`, change `"ok"` to `"OK"` and push | Red *Unit tests* stage |
| A2 | In the `Jenkinsfile`, change `python:3.12-slim` to `python:3.12-slimm` | Docker pull error |
| A3 | `docker stop jenkins-agent`, then build with `RUN_ON_AGENT=true` | Build waits forever: "Waiting for next available executor" |
| A4 | In `app/Dockerfile`, change `CMD` to `["python", "ap.py"]` | Build passes, smoke test fails |
| A5 | Delete the `agent-ssh` credential | Agent offline, auth error in node log |
| A6 | Add `sleep 1200` to a stage | Pipeline aborted by the timeout |
| A7 | Remove `--network lab-net` from `docker run` | curl cannot resolve the host |

Also practise:
- Writing a new pipeline from an empty file, without looking: parameters, `when`, `post`, `withCredentials`, `parallel` stages.
- Adding a `parallel` stage that runs lint and tests at the same time.
- Tagging the image with the short git SHA instead of the build number (`sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()`).
- Archiving a test report (`junit`) and an artifact (`archiveArtifacts`).

Hints: Console Output and the stage view first. A1–A2: read the first error line, not the last. A3/A5: the node's **Log** page. A4: `docker logs`. A6: `options { timeout }`. A7: `docker network inspect lab-net`.

---

## B. Docker

| # | Exercise |
|---|---|
| B1 | `docker run -d -p 8000:8000 lab-app:<n>` twice. Why does the second one fail? Fix it without stopping the first. |
| B2 | Container status is `unhealthy`. Find out why with `docker inspect --format '{{json .State.Health}}' <c>` |
| B3 | Disk is full of images: `docker system df`, then clean up safely (`docker image prune`, and when `-a` is dangerous) |
| B4 | Rewrite `app/Dockerfile` as a multi-stage build that runs tests in stage 1 and copies only `app.py` into the final image |
| B5 | Exec into a running container whose image has no shell. What are your options? (`docker cp`, `docker debug`, a sidecar with `--pid`/`--network container:`) |

---

## C. Linux (on the VM, after the Ansible run)

Inject each fault with `sudo`, then troubleshoot from `curl -k https://<VM_IP>/health`.

| # | Inject the fault | Expected symptom |
|---|---|---|
| C1 | `sudo systemctl stop labapp` | nginx returns **502 Bad Gateway** |
| C2 | `sudo sed -i 's/proxy_pass/proxy_pas/' /etc/nginx/sites-available/labapp && sudo systemctl reload nginx` | Reload fails; old config keeps running |
| C3 | `sudo chmod 000 /opt/labapp/app.py && sudo systemctl restart labapp` | Service crash loop |
| C4 | `sudo ufw allow 22/tcp && sudo ufw enable && sudo ufw deny 443/tcp` | HTTPS times out (SSH still works) |
| C5 | `sudo fallocate -l 10G /var/tmp/bigfile` | Disk full; services fail to write |
| C6 | Change `PORT=8000` to `PORT=9000` in `/etc/systemd/system/labapp.service`, then `daemon-reload` and restart | 502 again, but the service is "active" |
| C7 | `echo "127.0.0.1 github.com" \| sudo tee -a /etc/hosts` | `git clone` / `curl https://github.com` fails |

Toolkit to practise until it is automatic:
```bash
systemctl status labapp; journalctl -u labapp -n 50 --no-pager; journalctl -xe
sudo nginx -t; tail -f /var/log/nginx/error.log
ss -tulpn; curl -v http://127.0.0.1:8000/health; curl -vk https://localhost/
df -h; du -xh / --max-depth=1 2>/dev/null | sort -h | tail; ls -l; namei -l /opt/labapp/app.py
sudo ufw status verbose; ip a; ip r; dig github.com; cat /etc/hosts; getent hosts github.com
openssl s_client -connect localhost:443 -servername lab-vm.local </dev/null | openssl x509 -noout -subject -dates
```

Clean up after the drills: rerun `ansible-playbook site.yml`. Ansible should repair C2, C3 and C6 (note which ones it **cannot** repair, and why). Then `sudo ufw disable`, delete the big file, and edit `/etc/hosts`.

---

## D. Scripting (write from memory, about 15 minutes each)

1. **Bash:** `check_host.sh`. Warn if any filesystem is above 80%, if `nginx` or `labapp` is not active, or if `/health` does not return 200. Exit code ≠ 0 on any problem. Use `set -euo pipefail`.
2. **Bash:** rotate/clean up. Delete `*.log` files older than 7 days in a given directory. Support a `--dry-run` flag.
3. **Python:** parse `/var/log/nginx/access.log`. Print the top 5 IPs, the count per HTTP status code, and the percentage of 5xx responses.
4. **Python:** call `/health` every 5 s for 1 min. Print latency and status, and summarise min/avg/max latency at the end.

---

## E. Talk-through questions (answer out loud in 2 minutes each)

- A pipeline that was green yesterday is red today and nobody changed the code. What do you check, in order?
- Builds have become 3× slower over a month. How do you investigate?
- How would you move this lab's Jenkins setup to AKS (controller, agents as pods, persistent storage, ingress + TLS)?
- How do you manage secrets in Jenkins, Ansible (Vault) and Azure (Key Vault)?
- Terraform state got corrupted or locked. What do you do?
