// CI pipeline: lint, unit tests, image build, smoke test, optional push.
// Needs a Jenkins that can run "docker" (see docs/jenkins-setup.md).
pipeline {
    agent any

    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
        booleanParam(name: 'PUSH_IMAGE', defaultValue: false, description: 'Push the image to Docker Hub')
        string(name: 'DOCKERHUB_USER', defaultValue: '', description: 'Docker Hub user (used when PUSH_IMAGE is on)')
    }

    environment {
        IMAGE = 'edgeguard-vote-detector'
        TEST_IMAGE = "edgeguard-vote-detector-test:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build test image') {
            steps {
                sh 'docker build --target test -t "$TEST_IMAGE" .'
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm "$TEST_IMAGE" sh -c "ruff check . && ruff format --check ."'
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    docker rm -f "tests-$BUILD_NUMBER" >/dev/null 2>&1 || true
                    set +e
                    docker run --name "tests-$BUILD_NUMBER" "$TEST_IMAGE" pytest --junitxml=/tmp/junit.xml
                    status=$?
                    docker cp "tests-$BUILD_NUMBER:/tmp/junit.xml" junit.xml
                    docker rm "tests-$BUILD_NUMBER" >/dev/null
                    exit $status
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'junit.xml'
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --target runtime -t "$IMAGE:$BUILD_NUMBER" -t "$IMAGE:latest" .'
            }
        }

        stage('Smoke test image') {
            steps {
                sh '''
                    docker run --rm "$IMAGE:$BUILD_NUMBER" --version
                    docker run --rm "$IMAGE:$BUILD_NUMBER" demo | tee demo_scores.txt
                    grep -q vote_2_of_3 demo_scores.txt
                '''
            }
        }

        stage('Push to Docker Hub') {
            when {
                expression { params.PUSH_IMAGE && params.DOCKERHUB_USER?.trim() }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub',
                                                  usernameVariable: 'HUB_USER',
                                                  passwordVariable: 'HUB_TOKEN')]) {
                    sh '''
                        echo "$HUB_TOKEN" | docker login -u "$HUB_USER" --password-stdin
                        for tag in "$BUILD_NUMBER" latest; do
                            docker tag "$IMAGE:$tag" "$DOCKERHUB_USER/$IMAGE:$tag"
                            docker push "$DOCKERHUB_USER/$IMAGE:$tag"
                        done
                        docker logout
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker rmi "$TEST_IMAGE" >/dev/null 2>&1 || true'
            archiveArtifacts artifacts: 'demo_scores.txt', allowEmptyArchive: true
        }
    }
}
