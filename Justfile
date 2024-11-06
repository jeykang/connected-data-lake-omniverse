# Copyright (c) 2024 Ho Kim (ho.kim@ulagbulag.io). All rights reserved.
# Use of this source code is governed by a Apache-2.0 license that can be
# found in the LICENSE file.

# Load environment variables
set dotenv-load

# Configure environment variables
export NGC_CLI_BASE_URL := env_var_or_default('NGC_CLI_BASE_URL', 'https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli')
export NGC_CLI_HOME := env_var_or_default('NGC_CLI_HOME', './ngc-cli')
export NVIDIA_OMNIVERSE_KIT_HOME := env_var_or_default('NVIDIA_OMNIVERSE_KIT_HOME', '')

default: (run 'editor.base')

run TYPE="editor.base":
    @if [ ! -d "${NGC_CLI_HOME}" ]; then \
        echo '* Downloading NVIDIA NGC CLI' \
        && NGC_CLI_VERSION="$(curl -sL "${NGC_CLI_BASE_URL}/versions" | \
            grep -Po '"versionId"\: *"\K[0-9\.]+' | \
            sort -V | \
            tail -n1 \
        )" && \
            curl -L "${NGC_CLI_BASE_URL}/versions/${NGC_CLI_VERSION}/files/ngccli_linux.zip" | \
            busybox unzip - -d "$(dirname "${NGC_CLI_HOME}")" 'ngc-cli/*' \
            && chmod u+x "${NGC_CLI_HOME}/ngc" \
    ; fi

    @if [ "x${NVIDIA_OMNIVERSE_KIT_HOME}" = 'x' ]; then \
        NVIDIA_OMNIVERSE_KIT_HOME="$(find . -mindepth 1 -maxdepth 1 -name 'kit-sdk-*' -type d)" \
    ; fi && \
    if [ "x${NVIDIA_OMNIVERSE_KIT_HOME}" = 'x' ] || [ ! -d "${NVIDIA_OMNIVERSE_KIT_HOME}" ]; then \
        echo '* Downloading NVIDIA Omniverse Kit SDK' \
        && "${NGC_CLI_HOME}/ngc" registry resource download-version 'nvidia/omniverse/kit-sdk-linux' \
        && NVIDIA_OMNIVERSE_KIT_HOME="$(find . -mindepth 1 -maxdepth 1 -name 'kit-sdk-*' -type d)" \
        && NVIDIA_OMNIVERSE_KIT_FILE="$(find "${NVIDIA_OMNIVERSE_KIT_HOME}" -mindepth 1 -maxdepth 1 -name '*.zip' -type f)" \
        && busybox unzip "${NVIDIA_OMNIVERSE_KIT_FILE}" -d "${NVIDIA_OMNIVERSE_KIT_HOME}" -o \
        && rm "${NVIDIA_OMNIVERSE_KIT_FILE}" \
        && rm -f './app' \
        && ln -sf "x${NVIDIA_OMNIVERSE_KIT_HOME}" './app' \
    ; fi && \
    exec "${NVIDIA_OMNIVERSE_KIT_HOME}/omni.app.{{ TYPE }}.sh" \
        --enable 'nuscenes.viz' \
        --ext-folder './exts'
