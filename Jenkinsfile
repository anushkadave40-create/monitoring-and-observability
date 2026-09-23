pipeline {
    agent any

    environment {
        APP_NAME = "sre-demo"
        APP_VERSION = "1.0.${env.BUILD_NUMBER}"
        NAMESPACE = "student-03"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Building ${env.APP_NAME} version ${env.APP_VERSION}"
                sh 'echo "Simulating git checkout"'
            }
        }

        stage('Test') {
            steps {
                echo 'Running unit tests...'
                sh 'sleep 2 && echo "Tests: 15 passed, 0 failed"'
            }
        }

        stage('Build Image') {
            steps {
                echo "Building Docker image: ${env.APP_NAME}:${env.APP_VERSION}"
                sh 'echo "docker build -t ${APP_NAME}:${APP_VERSION} ."'
                sh 'echo "docker push registry/${APP_NAME}:${APP_VERSION}"'
            }
        }

        stage('Approval') {
            steps {
                input message: "Deploy ${APP_NAME}:${APP_VERSION} to production?",
                      ok: "Deploy"
            }
        }

        stage('Deploy to k8s') {
            steps {
                echo "Deploying to namespace: ${env.NAMESPACE}"
                sh """
                    echo "kubectl set image deployment/${APP_NAME} ${APP_NAME}=registry/${APP_NAME}:${APP_VERSION} -n ${NAMESPACE}"
                    echo "kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE}"
                """
            }
        }

        stage('Smoke Test') {
            steps {
                echo 'Running post-deploy smoke tests...'
                sh 'sleep 1 && echo "HTTP 200 OK — deployment healthy"'
            }
        }
    }

    post {
        success {
            echo "Deployed ${env.APP_NAME}:${env.APP_VERSION} successfully"
        }
        failure {
            echo "Deployment failed — rolling back"
            sh 'echo "kubectl rollout undo deployment/${APP_NAME} -n ${NAMESPACE}"'
        }
    }
}
