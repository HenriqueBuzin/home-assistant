pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {
        stage('Install') {
            when {
                expression { ['fln', 'cxs', 'fln-dev', 'cxs-dev'].contains(env.BRANCH_NAME) }
            }
            steps {
                sh '''
                    set -eu
                    docker compose version
                    echo 'Dependencias Node/npm sao instaladas no build multi-stage.'
                '''
            }
        }

        stage('Verify') {
            when {
                expression { ['fln', 'cxs', 'fln-dev', 'cxs-dev'].contains(env.BRANCH_NAME) }
            }
            steps {
                sh '''
                    set -eu
                    sh scripts/verify.sh
                    docker build --target verify --tag home-assistant/infra:verify .
                '''
            }
        }

        stage('Compose') {
            when {
                expression { ['fln', 'cxs', 'fln-dev', 'cxs-dev'].contains(env.BRANCH_NAME) }
            }
            steps {
                script {
                    def isDev = env.BRANCH_NAME.endsWith('-dev')
                    def site = env.BRANCH_NAME.replaceFirst(/-dev$/, '')
                    def project = "home-assistant-${site}${isDev ? '-dev' : ''}"
                    def composeFile = isDev ? 'docker-compose.yml' : 'docker-compose-prod.yml'

                    sh """
                        set -eu
                        project='${project}'
                        project_dir="/root/projects/\${project}"
                        env_file="/root/projects/envs/\${project}.env"

                        test -f "\$env_file"
                        install -d -m 0755 "\$project_dir"
                        find "\$project_dir" -mindepth 1 -maxdepth 1 ! -name '.env' -exec rm -rf -- {} +
                        cp -a "\$WORKSPACE"/. "\$project_dir"/
                        ln -sfn "\$env_file" "\$project_dir/.env"

                        cd "\$project_dir"
                        export COMPOSE_PROJECT_NAME="\$project"

                        config_root="\$(sed -n 's/^HA_CONFIG_ROOT=//p' .env | tail -n 1 | tr -d '\r')"
                        expected_config_root="/root/projects/volumes/\${project}/config"
                        [ "\$config_root" = "\$expected_config_root" ] || {
                          echo "HA_CONFIG_ROOT deve ser \$expected_config_root"
                          exit 1
                        }

                        docker run --rm \
                          --entrypoint mkdir \
                          -v /root/projects/volumes:/volumes \
                          home-assistant/infra:verify \
                          -p "/volumes/\${project}/config" "/volumes/\${project}/restore"

                        docker compose --env-file .env -f '${composeFile}' config --quiet
                    """
                }
            }
        }

        stage('Container') {
            when {
                expression { ['fln', 'cxs', 'fln-dev', 'cxs-dev'].contains(env.BRANCH_NAME) }
            }
            steps {
                script {
                    def isDev = env.BRANCH_NAME.endsWith('-dev')
                    def site = env.BRANCH_NAME.replaceFirst(/-dev$/, '')
                    def project = "home-assistant-${site}${isDev ? '-dev' : ''}"
                    def composeFile = isDev ? 'docker-compose.yml' : 'docker-compose-prod.yml'

                    sh """
                        set -eu
                        cd '/root/projects/${project}'
                        export COMPOSE_PROJECT_NAME='${project}'
                        docker compose --env-file .env -f '${composeFile}' build --pull backend
                    """
                }
            }
        }

        stage('Deploy') {
            when {
                expression { ['fln', 'cxs', 'fln-dev', 'cxs-dev'].contains(env.BRANCH_NAME) }
            }
            steps {
                script {
                    def isDev = env.BRANCH_NAME.endsWith('-dev')
                    def site = env.BRANCH_NAME.replaceFirst(/-dev$/, '')
                    def project = "home-assistant-${site}${isDev ? '-dev' : ''}"
                    def composeFile = isDev ? 'docker-compose.yml' : 'docker-compose-prod.yml'

                    sh """
                        set -eu
                        cd '/root/projects/${project}'
                        export COMPOSE_PROJECT_NAME='${project}'
                        docker network inspect proxy-network >/dev/null 2>&1 || docker network create proxy-network
                        docker compose --env-file .env -f '${composeFile}' down --timeout 30 || true
                        if ! docker compose --env-file .env -f '${composeFile}' up -d --remove-orphans; then
                          docker compose --env-file .env -f '${composeFile}' logs --tail=200 backend
                          exit 1
                        fi

                        attempts=0
                        until [ "\$attempts" -ge 30 ]; do
                          status="\$(docker compose --env-file .env -f '${composeFile}' ps --format json backend | grep -o '"Health":"[^"]*"' | head -1 || true)"
                          [ "\$status" = '"Health":"healthy"' ] && break
                          attempts=\$((attempts + 1))
                          sleep 10
                        done

                        [ "\$attempts" -lt 30 ] || {
                          docker compose --env-file .env -f '${composeFile}' logs --tail=200 backend
                          exit 1
                        }
                        docker run --rm --network proxy-network \
                          alpine:3.20 \
                          wget -q -O /dev/null "http://${project}:8123/"
                        docker compose --env-file .env -f '${composeFile}' ps
                    """
                }
            }
        }
    }
}
