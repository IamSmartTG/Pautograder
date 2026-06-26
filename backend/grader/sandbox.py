import os, tempfile, docker
from concurrent.futures import ThreadPoolExecutor

# ponytail: lazy-init so import succeeds without Docker running; tests patch this
_client = None
_executor = ThreadPoolExecutor(max_workers=4)


def run_in_sandbox(
    image: str,
    command: list[str],
    files: dict[str, bytes],
    timeout: int,
    network: str = "none",
    shm_size: str | None = None,
) -> dict:
    global _client
    if _client is None:
        _client = docker.from_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        for name, content in files.items():
            dest = os.path.join(tmpdir, name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(content)

        try:
            container = _client.containers.run(
                image=image,
                command=command,
                volumes={tmpdir: {"bind": "/submission", "mode": "rw"}},
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode=network,
                pids_limit=64,
                shm_size=shm_size,  # bigger /dev/shm for Chromium (browser graders)
                # ponytail: safe hardening only. cap_drop=ALL / non-root / read-only
                # rootfs deferred — they can break Chromium's sandbox + Playwright
                # writes and need a Docker test pass before enabling.
                security_opt=["no-new-privileges:true"],
                detach=True,
                remove=False,
            )
            try:
                result = container.wait(timeout=timeout)
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
                return {"stdout": stdout, "stderr": stderr, "exit_code": result["StatusCode"], "timed_out": False}
            except Exception:
                try:
                    container.kill()
                except Exception:
                    pass
                return {"stdout": "", "stderr": "Execution timed out", "exit_code": -1, "timed_out": True}
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        except Exception as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "timed_out": False}
