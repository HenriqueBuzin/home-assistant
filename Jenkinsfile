pipeline {
    agent any

    stages {
        stage('Deploy Home Assistant') {
            steps {
                script {

                    // 🔥 CORRETO para Multibranch
                    def branch = env.BRANCH_NAME

                    def projectMap = [
                        "fln"    : ["folder": "home-assistant-fln",     "service": "ha-fln"],
                        "cxs"    : ["folder": "home-assistant-cxs",     "service": "ha-cxs"],
                        "fln-dev": ["folder": "home-assistant-fln-dev", "service": "ha-fln-dev"],
                        "cxs-dev": ["folder": "home-assistant-cxs-dev", "service": "ha-cxs-dev"]
                    ]

                    echo "🚀 Branch detectada: ${branch}"

                    // ❌ bloqueia branches não mapeadas (importante)
                    if (!projectMap.containsKey(branch)) {
                        error "❌ Branch não suportada: ${branch}"
                    }

                    def folder = projectMap[branch].folder
                    def service = projectMap[branch].service

                    echo "📦 Projeto: ${folder}"
                    echo "🐳 Serviço: ${service}"

                    sh """
                    set -e

                    cd /root/projects/${folder}

                    echo "🔄 Atualizando código..."
                    git fetch origin
                    git reset --hard origin/${branch}
                    git clean -fd

                    echo "🔗 Aplicando .env..."
                    ln -sf /root/envs/${folder}.env .env

                    echo "🐳 Subindo container..."
                    docker compose up -d --build ${service}

                    echo "✅ Deploy concluído com sucesso!"
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🎉 Deploy OK - ${env.BRANCH_NAME}"
        }
        failure {
            echo "💥 Deploy FALHOU - ${env.BRANCH_NAME}"
        }
    }
}
