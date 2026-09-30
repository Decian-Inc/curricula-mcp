/* groovylint-disable LineLength */
def majorVersion = ''
def minorVersion = ''
def patchVersion = ''
def buildSkipped = false
def branchName = ''


pipeline {
    agent {
        label 'ubuntu22-vm'
    }
    options {
        disableConcurrentBuilds(abortPrevious: false)
    }
    environment {
        DOCKER_REGISTRY = 'nexus-registry.decian.net'
        IMAGE_NAME = 'curricula-mcp'
        // Read/write deploy key on Decian-Inc/curricula-mcp. Used for the job's SCM
        // checkout and for pushing the VERSION bump back.
        GIT_DEPLOY_KEY = 'curricula-mcp-deploy-key'
    }

    stages {
        stage('Skip?') {
        agent any
        steps {
            script {
                if (sh(script: "git log -1 --pretty=%B | fgrep -ie '[skip ci]' -e '[ci skip]'", returnStatus: true) == 0) {
                    def isManualTrigger = currentBuild.rawBuild.getCauses()[0].toString().contains('UserIdCause')
                    if (!isManualTrigger) {
                        currentBuild.result = 'SUCCESS'
                        currentBuild.description = 'Build skipped due to commit message'
                        buildSkipped = true
                        return
                    }
                }
            }
        }
        }
        stage('Checkout') {
            when {
                expression { return !buildSkipped }
            }
            steps {
                script {
                    def scmVars = checkout scm
                    // Plain Pipeline job (not multibranch): take the branch from the checkout's
                    // GIT_BRANCH, stripping the "origin/" prefix the git plugin adds.
                    branchName = (env.BRANCH_NAME ?: scmVars.GIT_BRANCH ?: '').replaceFirst(/^origin\//, '')
                    echo "Resolved branch: '${branchName}'"
                }
            }
        }

        stage('Version Management') {

            steps {
                script {
                    def version = readFile("${env.WORKSPACE}/VERSION").trim()
                    (majorVersion, minorVersion, patchVersion) = version.tokenize('.')

                    echo "Current Version: ${majorVersion}.${minorVersion}.${patchVersion}"

                    if (branchName in ['master', 'main'] && !buildSkipped) {
                        // Bump patch version; committed back in the last stage
                        patchVersion = patchVersion.toInteger() + 1
                        echo "New Version: ${majorVersion}.${minorVersion}.${patchVersion}"
                        sh "echo ${majorVersion}.${minorVersion}.${patchVersion} > VERSION"
                    }
                    currentBuild.displayName = "# ${majorVersion}.${minorVersion}.${patchVersion}.${env.BUILD_NUMBER} | ${branchName}"
                }
            }
        }

        stage('Build Push Docker image') {
            when {
                expression { return !buildSkipped }
            }
            steps {
                script {
                    def version = "${majorVersion}.${minorVersion}.${patchVersion}"
                    def branchTag = branchName.replaceAll("/", "-").toLowerCase()
                    def dockerTags = [
                        // Moving per-branch tag (master -> :master) that Deployments pull with
                        // imagePullPolicy: Always.
                        "${branchTag}",
                        // Immutable per-build tag, e.g. 0.1.4-master-12.
                        "${version}-${branchTag}-${env.BUILD_NUMBER}",
                        "${version}-${branchTag}"
                    ]

                    if (branchName in ['master', 'main']) {
                        dockerTags.add("${version}")
                        dockerTags.add("${majorVersion}.${minorVersion}")
                        dockerTags.add("${majorVersion}")
                        dockerTags.add("latest")
                    }

                    def dockerBuildCommandTags = dockerTags.collect { tag -> "-t $DOCKER_REGISTRY/$IMAGE_NAME:${tag}" }.join(' ')

                    // Dockerfile is at the repo root.
                    docker.withRegistry('https://nexus-registry.decian.net', 'nexus-docker-writer-username-password') {
                        sh """
                            docker build --push $dockerBuildCommandTags -f ./Dockerfile .
                        """
                    }
                }
            }
        }

        stage('Re-Commit Version Management') {
            when {
                expression { return !buildSkipped }
            }
            steps {
                script {
                    if (branchName in ['master', 'main']) {
                        sh "git add VERSION"
                        sh "git commit -m '[skip ci] Update VERSION'"
                        withCredentials([sshUserPrivateKey(credentialsId: env.GIT_DEPLOY_KEY, keyFileVariable: 'SSH_KEY')]) {
                            sh """
                                GIT_SSH_COMMAND='ssh -i \$SSH_KEY -o IdentitiesOnly=yes' git push ${scm.userRemoteConfigs[0].url.replace('https://github.com/', 'git@github.com:')} HEAD:${branchName}
                            """
                        }
                    }
                }
            }
        }
    }
}
