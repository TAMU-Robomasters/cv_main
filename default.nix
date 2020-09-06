# I don't fully understand what this does -- Jeff
{
    pkgs ? (import (import ./settings/nix/sources.nix).nixpkgs {})
}: pkgs.poetry2nix.mkPoetryApplication {
    projectDir = ./.;   
}