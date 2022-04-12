#!/usr/bin/env bash
# This script removes all Nix files.

GIT_ROOT=$(cd "${BASH_SOURCE%/*}" && git rev-parse --show-toplevel)
source "${GIT_ROOT}/nix/scripts/lib.sh"
source "${GIT_ROOT}/scripts/colors.sh"

nix_purge_multi_user_service_darwin() {
    pushd /Library/LaunchDaemons
    NIX_SERVICES=(org.nixos.darwin-store.plist org.nixos.nix-daemon.plist)
    for NIX_SERVICE in "${NIX_SERVICES[@]}"; do
        sudo launchctl remove "${NIX_SERVICE}"
    done
}

nix_purge_multi_user_service_linux() {
    NIX_SERVICES=(nix-daemon.service nix-daemon.socket)
    for NIX_SERVICE in "${NIX_SERVICES[@]}"; do
        sudo systemctl stop "${NIX_SERVICE}"
        sudo systemctl disable "${NIX_SERVICE}"
    done
    sudo systemctl daemon-reload
}

nix_purge_multi_user_users_darwin() {
    for NIX_USER in $(dscl . list /Users | grep nixbld); do
        sudo dscl . -delete "/Users/${NIX_USER}"
    done
    sudo dscl . -delete /Groups/nixbld
}

nix_purge_multi_user_users_linux() {
    for NIX_USER in $(awk -F: '/nixbld/{print $1}' /etc/passwd); do
        sudo userdel "${NIX_USER}"
    done
    sudo groupdel nixbld
}

nix_purge_multi_user_synthetic() {
    if grep nix /etc/synthetic.conf > /dev/null; then
        sed -i.bkp '/nix/d' /etc/synthetic.conf
        echo -e "${YLW}You will need to reboot your system!${RST}" >&2
    fi
}

nix_purge_multi_user() {
    if [[ $(uname -s) == "Darwin" ]]; then
        nix_purge_multi_user_service_darwin
        nix_purge_multi_user_users_darwin
        nix_purge_multi_user_synthetic
    else
        nix_purge_multi_user_service_linux
        nix_purge_multi_user_users_linux
    fi

    sudo rm -fr /etc/nix
    sudo rm -f /etc/profile.d/nix.sh*

    # Restore old shell profiles
    NIX_PROFILE_FILES=(
        /etc/bash.bashrc /etc/bashrc /etc/bash/bashrc
        /etc/zsh.zshhrc /etc/zshrc /etc/zsh/zshrc
    )
    for NIX_FILE in "${NIX_PROFILE_FILES[@]}"; do
        if [[ -f "${NIX_FILE}.backup-before-nix" ]]; then
            sudo mv -f "${NIX_FILE}.backup-before-nix" "${NIX_FILE}"
        fi
    done
}

nix_purge_user_profile() {
    sudo rm -rf \
        ~/.nix-* \
        ~/.cache/nix \
        ~/.config/nixpkgs \
        ${GIT_ROOT}/.nix-gcroots
}

nix_purge_root() {
    NIX_ROOT=$(nix_root)
    if [[ -z "${NIX_ROOT}" ]]; then
        echo -e "${RED}Unable to identify Nix root!${RST}" >&2
        exit 1
    fi
    sudo rm -fr "${NIX_ROOT}"
}

# Don't run anything if just sourced.
if (return 0 2>/dev/null); then
    echo -e "${YLW}Script sourced, not running purge.${RST}"
    return
fi

NIX_INSTALL_TYPE=$(nix_install_type)

if [[ "${1}" == "--force" ]] && [[ "${NIX_INSTALL_TYPE}" != "nixos" ]]; then
    echo -e "${YLW}Purge forced, no checks performed!${RST}" >&2
    nix_purge_multi_user
    nix_purge_user_profile
    nix_purge_root
    exit
fi

# Purging /nix on NixOS would be disasterous
if [[ "${NIX_INSTALL_TYPE}" == "nixos" ]]; then
    echo -e "${RED}You should not purge Nix files on NixOS!${RST}" >&2
    exit
elif [[ "${NIX_INSTALL_TYPE}" == "none" ]]; then
    echo -e "${YLW}Nothing to remove, Nix not installed.${RST}" >&2
    exit
elif [[ "${NIX_INSTALL_TYPE}" == "multi" ]]; then
    echo -e "${YLW}Detected multi-user Nix installation.${RST}" >&2
    nix_purge_multi_user
elif [[ "${NIX_INSTALL_TYPE}" == "single" ]]; then
    echo -e "${YLW}Detected single-user Nix installation.${RST}" >&2
    nix_purge_user_profile
fi
nix_purge_root

echo -e "${GRN}Purged all Nix files from your system.${RST}" >&2
