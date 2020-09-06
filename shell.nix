# Lets setup some definitions
let
    # niv should pin your current thing inside ./nix/sources
    # here we go and get that pinned version so we can pull packages out of it
    sources = import ./settings/nix/sources.nix;
    normalPackages = import sources.nixpkgs {};
    
    my-python-packages = python-packages: with python-packages; [ 
        opencv4
        numpy
        matplotlib
        pillow
        filterpy
        scikit-build
        scipy
        pyyaml
        regex
    ];
    python-with-my-packages = normalPackages.python3.withPackages my-python-packages;
# using those definitions
in
    # create a shell
    normalPackages.mkShell {
        
        # inside that shell, make sure to use these packages
        buildInputs = [
            # normalPackages.ffmpeg-full # this might help with opencv, not sure
            # normalPackages.cmake
            # python and venv
            
            python-with-my-packages
            # normalPackages.python3
            # normalPackages.poetry
            # normalPackages.python37Packages.setuptools
            # normalPackages.python37Packages.pip
            # normalPackages.python37Packages.virtualenv
            # normalPackages.python37Packages.opencv4
            # normalPackages.python37Packages.pyyaml
            # normalPackages.python37Packages.ruamel_yaml
            # normalPackages.python37Packages.matplotlib
            # normalPackages.python37Packages.pillow
            # normalPackages.python37Packages.filterpy
            # normalPackages.python37Packages.scikit-build
            # normalPackages.python37Packages.scipy
            
            # basic commandline tools
            # normalPackages.ripgrep
            # normalPackages.which
            # normalPackages.git
            # normalPackages.colorls
            # normalPackages.tree
            # normalPackages.less
            # normalPackages.niv
            # normalPackages.cacert # needed for niv
            # normalPackages.nix    # needed for niv
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
        # 
        # find and run all the startup scripts in alphabetical order
        # 
        for file in ./settings/shell_startup/*
        do
            # make sure its a file
            if [[ -f $file ]]; then
                source $file
            fi
        done
        '';
    }

