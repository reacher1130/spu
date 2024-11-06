set -ex

show_help() {
    echo "Usage: bash build.sh [OPTION]... -v {version}"
    echo "  -v  --version"
    echo "          the version to build with."
    echo "  -r  --reg"
    echo "          docker reg to upload."
    echo "  -l --latest"
    echo "          tag this version as latest."
}

if [[ "$#" -lt 2 ]]; then
    show_help
    exit
fi

while [[ "$#" -ge 1 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift
            if [[ "$#" -eq 0 ]]; then
                echo "Version shall not be empty."
                echo ""
                show_help
                exit 1
            fi
            shift
        ;;
        -r|--reg)
            DOCKER_REG="$2"
            shift
            if [[ "$#" -eq 0 ]]; then
                echo "Docker reg shall not be empty."
                echo ""
                show_help
                exit 1
            fi
            shift
        ;;
        -l|--latest)
            LATEST=1
            shift
        ;;
        *)
            echo "Unknown argument passed: $1"
            exit 1
        ;;
    esac
done


if [[ -z ${VERSION} ]]; then 
    echo "Please specify the version."
    exit 1
fi

GREEN="\033[32m"
NO_COLOR="\033[0m"

IMAGE_NAME=spu-dev-anolis8:${VERSION}
echo -e "Building ${GREEN}${IMAGE_TAG}${NO_COLOR}"
(rm -rf dist/ build/)

docker run -it --rm -e SPU_BUILD_DOCKER_NAME=${IMAGE_NAME} --mount type=bind,source="$(pwd)/../../spu",target=/home/admin/src -w /home/admin --cap-add=SYS_PTRACE --security-opt seccomp=unconfined --cap-add=NET_ADMIN --privileged=true secretflow/release-ci:latest /home/admin/src/dev/entry.sh