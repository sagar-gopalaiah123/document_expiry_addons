pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'GitHub checkout completed'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Check Odoo Module') {
            steps {
                sh 'ls -la document_expiry_engine'
                sh 'cat document_expiry_engine/__manifest__.py'
            }
        }

    }
}
