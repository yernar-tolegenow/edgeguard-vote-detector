# Jenkins controller with the Docker CLI inside, so pipeline stages can run
# "docker build" and "docker run" through the host's Docker socket.
# The CLI is copied from the official docker:cli image (no apt needed).
FROM jenkins/jenkins:lts-jdk21
USER root
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker
# Lab setup: runs as root so it can use /var/run/docker.sock without group tuning.
# For anything beyond a local lab, add the jenkins user to the docker group instead.
