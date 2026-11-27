pipeline {
    agent {
        label 'devops'
    }

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    stages {
        stage('Codigo fuente') {
            steps {
                deleteDir()
                sh 'git log -1 --oneline'
            }
        }

        stage('Entorno de pruebas') {
            steps {
                sh 'docker build -f Dockerfile.ci -t devops-manager-ci:1.0 .'
            }
        }

        stage('Pruebas unitarias') {
            steps {
                sh 'docker run --rm devops-manager-ci:1.0'
            }
        }

        stage('Analisis estatico') {
            steps {
                sh 'docker run --rm devops-manager-ci:1.0 bandit -r src app.py'
            }
        }

        stage('Auditoria de dependencias') {
            steps {
                sh 'docker run --rm devops-manager-ci:1.0 pip-audit -r requirements.txt'
            }
        }

        stage('Construccion Docker') {
            steps {
                sh 'docker build -t devops-manager:ci-${BUILD_NUMBER} .'
            }
        }

        stage('Escaneo de vulnerabilidades') {
            steps {
                sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v trivy_cache:/root/.cache/ \
                      aquasec/trivy:0.76.2 image \
                      --image-src docker \
                      --scanners vuln \
                      --severity HIGH,CRITICAL \
                      --exit-code 1 \
                      --timeout 10m \
                      devops-manager:ci-${BUILD_NUMBER}
                '''
            }
        }

        stage('Deteccion de secretos') {
            steps {
                sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v trivy_cache:/root/.cache/ \
                      aquasec/trivy:0.76.2 image \
                      --image-src docker \
                      --scanners secret \
                      --exit-code 1 \
                      devops-manager:ci-${BUILD_NUMBER}
                '''
            }
        }
        stage('Despliegue automatico') {
            steps {
                sh 'sh scripts/desplegar.sh devops-manager:ci-${BUILD_NUMBER}'
            }
        }

        stage('Verificacion HTTP') {
            steps {
                sh '''
                    docker run --rm --network host devops-manager:ci-${BUILD_NUMBER} python -c 'import urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8080/", timeout=5); print("HTTP:", r.status); assert r.status == 200'
                '''
            }
        }

    }

    post {
        success {
            echo 'DevOps Manager: verificaciones completadas correctamente.'
        }

        failure {
            echo 'DevOps Manager: pipeline detenido por errores.'
        }
    }
}
