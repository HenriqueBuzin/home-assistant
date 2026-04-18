pipeline {
    agent any

    stages {
        stage('Deploy Home Assistant') {
            steps {
                script {

                    def branch = env.GIT_BRANCH.replace("origin/", "")

                    def projectMap = [
                        "fln": ["folder": "home-assistant-fln", "service": "ha-fln"],
                        "cxs": ["folder": "home-assistant-cxs", "service": "ha-cxs"],
                        "fln-dev": ["folder": "home-assistant-fln-dev", "service": "ha-fln-dev"],
                        "cxs-dev": ["folder": "home-assistant-cxs-dev", "service": "ha-cxs-dev"]
                    ]

                    echo "Branch: ${branch}"

                    if (projectMap.containsKey(branch)) {

                        def folder = projectMap[branch].folder
                        def service = projectMap[branch].service

                        sh """
                        cd /root/projects/${folder}

                        git fetch origin
                        git reset --hard origin/${branch}
                        git clean -fd

                        # 🔗 garante o .env correto
                        ln -sf /root/envs/${folder}.env .env

                        # 🔥 sobe só o serviço correto
                        docker compose up -d --build ${service}
                        """
                    } else {
                        echo "Branch não suportada: ${branch}"
                    }
                }
            }
        }
    }
}
