pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('docker-hub-creds')
        IMAGE_NAME = 'keerthanavishnu/todo-app'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/keerthi020798-spec/todo-app.git'
            }
        }

        stage('Build Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} ."
            }
        }

        stage('Test') {
            steps {
                sh """
                    docker run -d --name test-todo -p 5001:5000 -e DB_HOST=localhost ${IMAGE_NAME}:${BUILD_NUMBER} || true
                    sleep 5
                    docker ps -a | grep test-todo
                    docker rm -f test-todo || true
                """
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh "echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin"
                sh "docker push ${IMAGE_NAME}:${BUILD_NUMBER}"
            }
        }

        stage('Update Manifest') {
            steps {
                sh "sed -i 's|image: keerthanavishnu/todo-app:.*|image: keerthanavishnu/todo-app:${BUILD_NUMBER}|' todo-deployment.yaml"
            }
        }

        stage('Deploy') {
            steps {
                sh "kubectl apply -f postgres-deployment.yaml"
                sh "kubectl apply -f postgres-service.yaml"
                sh "kubectl apply -f todo-deployment.yaml"
                sh "kubectl apply -f todo-service.yaml"
                sh "kubectl rollout restart deployment todo-app"
            }
        }
    }
}
