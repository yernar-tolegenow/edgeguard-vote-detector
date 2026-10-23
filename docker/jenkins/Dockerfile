# Jenkins controller with the Docker CLI inside, so pipeline stages can run
# "docker build" and "docker run" through the host's Docker socket.
FROM jenkins/jenkins:lts-jdk21
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*
# Lab setup: runs as root so it can use /var/run/docker.sock without group tuning.
# For anything beyond a local lab, add the jenkins user to the docker group instead.
