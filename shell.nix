# Lets setup some definitions
let
    # niv should pin your current thing inside ./nix/sources
    # here we go and get that pinned version so we can pull packages out of it
    sources = import ./nix/sources.nix;
    normalPackages = import sources.nixpkgs {};
    
# using those definitions
in
    # create a shell
    normalPackages.mkShell {
        
        # inside that shell, make sure to use these packages
        buildInputs = [
            normalPackages.cmake
            # python an venv
            normalPackages.python37
            normalPackages.python37Packages.setuptools
            normalPackages.python37Packages.pip
            normalPackages.python37Packages.virtualenv
            # basic commandline tools
            normalPackages.ripgrep
            normalPackages.which
            normalPackages.git
            normalPackages.colorls
            normalPackages.tree
            normalPackages.less
            normalPackages.niv
            # 
            # how to add packages?
            # 
            # to find package verisons use:
            #     nix-env -qP --available PACKAGE_NAME_HERE | cat
            # ex:
            #     nix-env -qP --available opencv
            # to add those specific versions find the nixpkgs.STUFF 
            # and add it here^ as normalPackages.STUFF
            # ex find:
            #     nixpkgs.python38Packages.opencv3  opencv-3.4.8
            # ex add:
            #     normalPackages.python38Packages.opencv3
            # 
            # NOTE: some things (like setuptools) just don't show up in the 
            # search results for some reason, and you just have to guess and check 🙃 
        ];
        
        shellHook = ''
        
        # asthetics
        PS1="∫"
        alias ls="ls --color"
        
        #
        # use venv
        #
        ls .venv &>/dev/null || python -m venv .venv
        source .venv/bin/activate
        echo "============================================="
        echo "installing pip modules"
        echo "============================================="
        pip install -r requirements.txt
        # use the project directory
        PYTHONPATH="$PYTHONPATH:$PWD"
        
        # setup local commands
        PATH="$PWD/commands:$PATH"
        echo ""
        echo ""
        echo "available commands:"
        ls -1 ./commands | sed 's/^/    /'
        alias help="./commands/help" # overrides default bash "help"
        echo ""
        '';

        # Environment variables
        # PYTHONPATH=".";
        # # note the ./. acts like $PWD
        # FOO = toString ./. + "/foobar";
    }

