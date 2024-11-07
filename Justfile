# Copyright (c) 2024 Ho Kim (ho.kim@ulagbulag.io). All rights reserved.
# Use of this source code is governed by a Apache-2.0 license that can be
# found in the LICENSE file.

# Load environment variables
set dotenv-load

# Configure environment variables
export NGC_CLI_BASE_URL := env_var_or_default('NGC_CLI_BASE_URL', 'https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli')
export NGC_CLI_HOME := env_var_or_default('NGC_CLI_HOME', './ngc-cli')
export NVIDIA_OMNIVERSE_KIT_HOME := env_var_or_default('NVIDIA_OMNIVERSE_KIT_HOME', '')

# Configure target-dependent variables
TARGET_ARCH := if arch() == "x86_64" {
        "amd64"
    } else if arch() == "arm64" {
        "arm64"
    } else {
        error("Unsupported architecture: " + arch())
    }
TARGET_OS := if os() == "linux" {
        "linux"
    } else if os() == "macos" {
        "macos"
    } else if os() == "windows" {
        "windows"
    } else {
        error("Unsupported OS: " + os())
    }

default: (run 'editor.base')

run TYPE="editor.base":
    @if [ ! -d "${NGC_CLI_HOME}" ]; then \
        if which ngc >/dev/null 2>/dev/null; then \
            mkdir -p "${NGC_CLI_HOME}" \
            && exec true \
        ; fi \
        && echo '* Downloading NVIDIA NGC CLI' \
        && NGC_CLI_VERSION="$(curl -sL "${NGC_CLI_BASE_URL}/versions" | \
            grep -Po '"versionId"\: *"\K[0-9\.]+' | \
            sort -V | \
            tail -n1 \
        )" && \
            if [ "x{{ TARGET_OS }}" = 'xlinux' ]; then \
                NGC_CLI_URL='' \
                && if [ "x{{ TARGET_ARCH }}" = 'xamd64' ]; then \
                    NGC_CLI_URL="${NGC_CLI_BASE_URL}/versions/${NGC_CLI_VERSION}/files/ngccli_linux.zip" \
                ; elif [ "x{{ TARGET_ARCH }}" = 'xarm64' ]; then \
                    NGC_CLI_URL="${NGC_CLI_BASE_URL}/versions/${NGC_CLI_VERSION}/files/ngccli_arm64.zip" \
                ; fi \
                && curl -L "${NGC_CLI_URL}" | busybox unzip - -d "$(dirname "${NGC_CLI_HOME}")" 'ngc-cli/*' \
                && chmod u+x "${NGC_CLI_HOME}/ngc" \
            ; elif [ "x{{ TARGET_OS }}" = 'xmacos' ] || [ "x{{ TARGET_OS }}" = 'xwindows' ]; then \
                echo '* Unattended installation of "ngc-cli" is not supported on your OS.' >&2 \
                && echo '  Please visit and install the proper "ngc-cli" on your machine.' >&2 \
                && echo '  Link: "https://org.ngc.nvidia.com/setup/installers/cli"' >&2 \
                && exit 1 \
            ; fi \
    ; fi

    @if [ "x${NVIDIA_OMNIVERSE_KIT_HOME}" = 'x' ]; then \
        NVIDIA_OMNIVERSE_KIT_HOME='./app' \
    ; fi && \
    if [ "x${NVIDIA_OMNIVERSE_KIT_HOME}" = 'x' ] || [ ! -d "${NVIDIA_OMNIVERSE_KIT_HOME}" ]; then \
        echo '* Downloading NVIDIA Omniverse Kit SDK' \
        && if [ -f "${NGC_CLI_HOME}/ngc" ]; then \
            NGC_CLI_PATH="${NGC_CLI_HOME}/ngc" \
        ; else \
            NGC_CLI_PATH="$(which ngc)" \
        ; fi \
        && "${NGC_CLI_PATH}" registry resource download-version 'nvidia/omniverse/kit-sdk-{{ TARGET_OS }}' \
        && NVIDIA_OMNIVERSE_KIT_HOME="$(find . -mindepth 1 -maxdepth 1 -name 'kit-sdk-*' -type d)" \
        && NVIDIA_OMNIVERSE_KIT_FILE="$(find "${NVIDIA_OMNIVERSE_KIT_HOME}" -mindepth 1 -maxdepth 1 -name '*.zip' -type f)" \
        && busybox unzip "${NVIDIA_OMNIVERSE_KIT_FILE}" -d "${NVIDIA_OMNIVERSE_KIT_HOME}" -o \
        && rm "${NVIDIA_OMNIVERSE_KIT_FILE}" \
        && rm -rf './app' \
        && mv "${NVIDIA_OMNIVERSE_KIT_HOME}" './app' \
        && NVIDIA_OMNIVERSE_KIT_HOME='./app' \
    ; fi && \
    if [ "x{{ TARGET_OS }}" = 'xwindows' ]; then \
        NVIDIA_OMNIVERSE_KIT_EXT=".bat" \
    ; else \
        NVIDIA_OMNIVERSE_KIT_EXT=".sh" \
    ; fi && \
    NVIDIA_OMNIVERSE_KIT_CMD="${NVIDIA_OMNIVERSE_KIT_HOME}/omni.app.{{ TYPE }}${NVIDIA_OMNIVERSE_KIT_EXT}" \
    && exec "${NVIDIA_OMNIVERSE_KIT_CMD}" \
        --enable 'nuscenes.viz' \
        --ext-folder './exts'
