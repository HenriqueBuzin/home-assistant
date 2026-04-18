pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {
        stage('Deploy Home Assistant') {
            steps {
                script {

                    def branch = env.BRANCH_NAME

                    def projectMap = [
                        "fln"    : ["folder": "home-assistant-fln",     "service": "ha-fln"],
                        "cxs"    : ["folder": "home-assistant-cxs",     "service": "ha-cxs"],
                        "fln-dev": ["folder": "home-assistant-fln-dev", "service": "ha-fln-dev"],
                        "cxs-dev": ["folder": "home-assistant-cxs-dev", "service": "ha-cxs-dev"]
                    ]

                    echo "🚀 Branch detectada: ${branch}"

                    if (branch == 'main') {
                        echo "✅ Branch main - sem deploy"
                        return
                    }

                    if (!projectMap.containsKey(branch)) {
                        echo "⚠️ Branch ignorada: ${branch}"
                        return
                    }

                    def folder = projectMap[branch].folder
                    def service = projectMap[branch].service

                    sh """
                    set -e

                    cd /root/projects/${folder}

                    echo "🔄 Atualizando código..."
                    git fetch origin
                    git reset --hard origin/${branch}
                    git clean -fd

                    echo "🔗 Aplicando .env..."
                    ln -sf /root/envs/${folder}.env .env

                    echo "🛑 Derrubando serviço antigo..."
                    docker compose down || true

                    echo "🐳 Subindo serviço..."
                    docker compose up -d --build ${service}

                    echo "✅ Deploy concluído!"
                    """
                }
            }
        }
    }
}
