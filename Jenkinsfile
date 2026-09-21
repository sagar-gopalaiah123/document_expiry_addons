pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out Odoo source code'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Start CI Environment') {
            steps {
                echo 'Starting PostgreSQL and Odoo CI containers'

                sh '''
                    docker compose -f docker-compose.ci.yml up -d
                '''
            }
        }

        stage('Check CI Environment') {
            steps {
                echo 'Checking container status'

                sh '''
                    docker compose -f docker-compose.ci.yml ps
                '''
            }
        }

        stage('Install Odoo Module') {
            steps {
                echo 'Installing document_expiry_engine'

                sh '''
                    docker compose -f docker-compose.ci.yml exec -T odoo \
                    odoo \
                    -d test_db \
                    -i document_expiry_engine \
                    --stop-after-init
                '''
            }
        }

    }

    post {
        always {
            echo 'Cleaning up CI environment'

            sh '''
                docker compose -f docker-compose.ci.yml down -v
            '''
        }

        success {
            echo 'Odoo CI pipeline completed successfully.'
        }

        failure {
            echo 'Odoo CI pipeline FAILED.'
        }
    }
}