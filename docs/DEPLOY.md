# Deploying Pautograder on a VM (full stack with grading)

This runs the whole app — UI, API, and Docker-sandboxed grading — on a single Linux VM with Docker Compose. Works on any VPS; the **Oracle Cloud "Always Free"** ARM VM (up to 4 cores / 24 GB) runs it for free.

## How it fits together

```
            :80
  browser ───────► web (nginx)  ──/api──►  backend (FastAPI)
                   serves React            │ docker.sock
                                           ▼
                                   host Docker daemon
                                           │ spawns one per submission
                                           ▼
                        pautograder-python-sandbox / -browser-sandbox
```

- **web** — nginx serves the built React bundle and reverse-proxies `/api` to the backend (same-origin, so no CORS).
- **backend** — FastAPI. To grade, it launches a fresh sandbox container per submission **on the host Docker daemon** via the mounted socket (Docker-out-of-Docker).

## The one thing people get wrong: the scratch path

The backend writes each submission's files to a temp dir, then bind-mounts that dir into the sandbox container. But the sandbox container is created by the **host** daemon, so the mount source is resolved **on the host**, not inside the backend container. If the path only exists inside the backend container, the sandbox mounts an empty dir and every grade fails.

The fix (already wired in `docker-compose.yml`): bind-mount a host dir at the **identical path** inside the backend container, and point `TMPDIR` at it.

```yaml
environment:
  - TMPDIR=/srv/pautograder/scratch
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
  - /srv/pautograder/scratch:/srv/pautograder/scratch   # same path both sides
```

No code change needed — `sandbox.py` uses `tempfile.TemporaryDirectory()`, which honors `TMPDIR`.

## Prerequisites

- A Linux VM (Ubuntu 22.04+). ARM64 is fine — all base images are multi-arch.
- Docker Engine + the Compose plugin:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER && newgrp docker   # run docker without sudo
  ```

## Deploy

```bash
git clone https://github.com/IamSmartTG/Pautograder.git
cd Pautograder

# 1. Host scratch dir (must match the compose path)
sudo mkdir -p /srv/pautograder/scratch
sudo chmod 777 /srv/pautograder/scratch

# 2. Build the sandbox images on the host daemon (the backend launches these by name)
docker build -t pautograder-python-sandbox  docker/python-sandbox/
docker build -t pautograder-browser-sandbox docker/browser-sandbox/    # large; minutes

# 3. Internal (no-internet) network used by webapp grading
docker network create --internal pautograder_sandbox

# 4. Build and start the stack
docker compose up -d --build
```

Open `http://<vm-ip>/`. The problem grid should load; algorithm submissions grade immediately.

Update later with `git pull && docker compose up -d --build`.

## Security — read before exposing publicly

- **The socket mount = host root.** A container with `/var/run/docker.sock` can fully control the host. The backend orchestrates grading (the untrusted code runs in *separate* sandbox containers), but treat the backend as a high-value target: keep its image minimal, don't add untrusted code paths to it.
- **Finish W2 sandbox hardening first.** This service runs arbitrary student code. Before public exposure, complete the deferred hardening in `backend/grader/sandbox.py` (`cap_drop=["ALL"]`, non-root user, read-only rootfs) and verify it against `pautograder-browser-sandbox`. See `docs/RUNNING.md`.
- **Firewall.** Only expose port 80/443. Put a TLS-terminating proxy (Caddy/Traefik) in front for HTTPS if this is more than a demo.

## Oracle Cloud "Always Free" notes

- Pick an **Ampere A1 (ARM)** instance — that's the free one. Ubuntu 22.04.
- Opening port 80 needs **two** steps:
  1. **VCN ingress rule** — add a security-list rule allowing TCP 80 (and 443) from `0.0.0.0/0`.
  2. **Host firewall** — Oracle's Ubuntu image ships locked-down iptables:
     ```bash
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo netfilter-persistent save
     ```

## Troubleshooting

- **Algorithm grades work, browser ones fail.** `--no-sandbox` and `shm_size=512m` are already wired into both browser graders. If Chromium still won't launch, confirm the `pautograder-browser-sandbox` image built fully and the VM has enough RAM/swap; bump `shm_size` further in `backend/grader/sandbox.py`.
- **Every grade fails with a mount/empty-dir error.** The scratch path doesn't match — confirm both the `TMPDIR` env and the `volumes` entry use the exact same path, and that the host dir exists and is writable.
- **`pautograder_sandbox` network not found.** Run step 3; the backend references it by exact name for webapp grading.
- **Browser image build is slow / OOMs.** It's large; give the VM swap or build it once and let it cache.

## Simpler alternative (no socket mount)

If the Docker-socket exposure worries you, run the **backend directly on the host** (a `uvicorn` systemd unit in a venv) so its temp dirs are already host paths — then grading "just works" with no scratch-path trick — and containerize only nginx for the frontend. More moving parts to manage, smaller blast radius.
