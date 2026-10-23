# Jenkins CI pipeline: setup on Ubuntu

This guide starts Jenkins in Docker on one computer and connects it to the repository.
The pipeline is in `Jenkinsfile`. Every step runs in containers built from the `Dockerfile`.

## 1. Check Docker

```bash
docker --version
docker run --rm hello-world
```

If the second command fails with "permission denied", add yourself to the docker group, then log out and in:

```bash
sudo usermod -aG docker $USER
```

## 2. Start Jenkins

```bash
cd docker/jenkins
docker compose up -d --build
docker logs jenkins 2>&1 | grep -A2 "initial admin password"   # first password
```

Open <http://localhost:8080>, paste the password, choose **Install suggested plugins**, and create an admin user.

Check that Jenkins can use Docker:

```bash
docker exec jenkins docker version
```

## 3. Create the pipeline job

1. **New Item**, name `edgeguard-vote-detector`, type **Pipeline**.
2. Pipeline section: **Pipeline script from SCM**, SCM **Git**.
3. Repository URL: `https://github.com/yernar-tolegenow/edgeguard-vote-detector.git` (public, no credentials needed).
4. Branch: `*/main`. Script Path: `Jenkinsfile`. Save.
5. Click **Build Now** once. The `Jenkinsfile` registers the trigger and the parameters.

## 4. What the pipeline does

| Stage | What happens |
|---|---|
| Checkout | Gets the code from Git |
| Build test image | `docker build --target test` |
| Lint | `ruff check` and `ruff format --check` in a container |
| Unit tests | `pytest` (27 tests) in a container; the result is shown in Jenkins |
| Build image | `docker build --target runtime`, tags `:<build number>` and `:latest` |
| Smoke test image | Runs `edgeguard demo` in the new image and checks the output |
| Push to Docker Hub | Only if `PUSH_IMAGE` is on (optional) |

New commits start a build within about two minutes (the job checks Git every two minutes).

## 5. Optional: push the image to Docker Hub

1. Create a free account and an access token on hub.docker.com (Account settings, Security).
2. In Jenkins: **Manage Jenkins, Credentials, Global, Add credentials**, kind *Username with password*, ID `dockerhub`, password is the token.
3. **Build with Parameters**: tick `PUSH_IMAGE`, enter `DOCKERHUB_USER`.

## 6. Run the image by hand

```bash
docker run --rm edgeguard-vote-detector              # demo
docker run --rm edgeguard-vote-detector --version
```

## Troubleshooting

- `docker: not found` inside a stage: rebuild with `docker compose up -d --build` so the Docker CLI is in the image.
- The Jenkins image build hangs on `apt` or `Ign:` lines: the image no longer uses apt (it copies the Docker CLI from `docker:cli`). Stop the build with Ctrl+C and run the build again.
- `permission denied ... docker.sock`: the compose file runs Jenkins as root for this lab; do not remove `user: root`.
- Nothing starts after a commit: check **Polling Log** in the job menu.
