#!/usr/bin/env bash
user="xavier3"
echo 'onboot script works'  >  "/home/$user/.boot.log"
"/home/$user/.nix-profile/bin/zsh" "/home/$user/boot.sh"  &>> "/home/$user/.boot.log"