# keychain is mac-os specific, just FYI
path_to_keychain="$HOME/Library/Keychains/"
if [[ -d "$path_to_keychain" ]]; then
    mkdir -p "$PROJECTR_HOME/Library/"
    # link all the keys
    ln -sf "$path_to_keychain" "$PROJECTR_HOME/Library/"
fi

# Make sure the user doesn't accidentally commit their keys/passwords!!
./settings/commands/.add_to_gitignore "$PROJECTR_HOME/Library/Keychains"