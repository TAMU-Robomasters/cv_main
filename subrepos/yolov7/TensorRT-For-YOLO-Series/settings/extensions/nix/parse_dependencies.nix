# 
# summary 
#     this file exports a function that does a few basic things 
#     1. parses the nix.toml file and return nix package objects
#     2. exports some basic information about the package dependencies to a json file
#     3. returns a "main" object that has all the basic builtin or builtin-like functionality
(rec {
    # 
    # create a standard library for convienience 
    # 
    frozenStd = (builtins.import 
        (builtins.fetchTarball
            ({url="https://github.com/NixOS/nixpkgs/archive/a7ecde854aee5c4c7cd6177f54a99d2c1ff28a31.tar.gz";})
        )
        ({})
    );
    main = (frozenStd.lib.mergeAttrs
        (frozenStd.lib.mergeAttrs
            (frozenStd.buildPackages) # <- for fetchFromGitHub, installShellFiles, getAttrFromPath, etc 
            (frozenStd.lib.mergeAttrs
                ({ stdenv = frozenStd.stdenv; })
                (frozenStd.lib) # <- for mergeAttrs, optionals, getAttrFromPath, etc 
            )
        )
        (builtins) # <- for import, fetchTarball, etc 
    );
    pathToThisFile = (builtins.getEnv
        "__FORNIX_NIX_MAIN_CODE_PATH"
    );
    # 
    # pull info from the config files
    # 
    nixSettings = (main.fromTOML
        (main.readFile 
            ./settings.toml
        )
    );
    # 
    # load the nix.toml cause were going to extract basically everything from there
    # 
    packageToml = (main.fromTOML
        (main.readFile
            ./nix.toml
        )
    );
    # 
    # load the store with all the packages, and load it with the config
    # 
    defaultFrom = (main.fetchTarball
        ({url="https://github.com/NixOS/nixpkgs/archive/${nixSettings.defaultFrom}.tar.gz";})
    );
    mainPackages = (main.import
        (defaultFrom)
        ({ config = nixSettings.config;})
    );
    packagesForThisMachine = (main.filter
        (eachPackage:
            (main.all
                # if all are true
                (x: x)
                (main.optionals
                    # if package depends on something
                    (main.hasAttr "onlyIf" eachPackage)
                    # basically convert something like ["stdev", "isLinux"] to main.stdenv.isLinux
                    (main.map
                        (eachCondition:
                            (main.getAttrFromPath
                                (eachCondition)
                                (main)
                            )
                        )
                        (eachPackage.onlyIf)
                    )
                )
            )
        )
        (packageToml.packages)
    );
    # 
    # reorganize the list of packages from:
    #    [ { load: "blah", from:"blah-hash" }, ... ]
    # into a list like:
    #    [ { name: "blah", commitHash:"blah-hash", source: (*an object*) }, ... ]
    #
    tomlPackagesWithSources = (main.map
        (each: 
            ({
                name = (main.concatMapStringsSep
                    (".")
                    (each: each)
                    (each.load)
                );
                commitHash = each.from;
                asNativeBuildInput = (
                    (main.hasAttr
                        ("asNativeBuildInput")
                        (each)
                    )
                    &&
                    each.asNativeBuildInput
                );
                value =
                    # if it says where (e.g. from)
                    if 
                        (main.hasAttr
                            ("from")
                            (each)
                        )
                    # then load it from that place
                    then 
                        (rec {
                            package = (main.getAttrFromPath
                                (each.load)
                                (main.import
                                    # if its a string, assume its a nixpkg commit hash
                                    (
                                        if 
                                            (main.isString
                                                (each.from)
                                            )
                                        then
                                            (main.fetchTarball
                                                ({url="https://github.com/NixOS/nixpkgs/archive/${each.from}.tar.gz";})
                                            )
                                        # otherwise assume its the details for a github repo
                                        else
                                            (main.fetchGit
                                                (each.from.fetchGit)
                                            )
                                    )
                                    (
                                        if 
                                            (
                                                (main.isString
                                                    (each.from)
                                                )
                                                ||
                                                (!main.hasAttr
                                                    ("options")
                                                    (each.from)
                                                )
                                            )
                                        then
                                            ({})
                                        # otherwise assume its the details for a github repo
                                        else
                                            (each.from.options)
                                    )
                                )
                            );
                            return = (
                                if 
                                    (main.hasAttr
                                        ("override")
                                        (each)
                                    )
                                then
                                    (package.override
                                        (each.override)
                                    )
                                else
                                    package
                            );
                        }.return)
                    # otherwise just default to getting it from mainPackages
                    else 
                        (main.getAttrFromPath
                            (each.load)
                            (mainPackages)
                        )
                ;
            })
        )
        (packagesForThisMachine)
    );
    listedDepedencyPackages = (main.listToAttrs 
        (tomlPackagesWithSources)
    );
    packages = (main.mergeAttrs
        mainPackages
        listedDepedencyPackages
    );
    tomlAndBuiltinPackagesWithSources = (tomlPackagesWithSources ++ 
        [  
            {
                name = "glib";
                value = packages.glib;
            }
            {
                name = "cc";
                value = main.stdenv.cc.cc;
            }
        ]
    );
    buildInputs = (main.map
        (each: each.value)
        (main.filter
            (each: !each.asNativeBuildInput)
            (tomlPackagesWithSources)
        )
    );
    nativeBuildInputs = (main.map
        (each: each.value)
        (main.filter
            (each: each.asNativeBuildInput)
            (tomlPackagesWithSources)
        )
    );
    depedencyPackages = (main.listToAttrs 
        (tomlAndBuiltinPackagesWithSources)
    );
    packagePathsAsJson = (main.toJSON
        ({
            packagePathFor = depedencyPackages;
            libPathFor = (main.listToAttrs
                (main.map
                    (each:
                        ({
                            name = each.name;
                            value = "${main.makeLibraryPath [ each.value ]}";
                        })
                    )
                    (tomlAndBuiltinPackagesWithSources)
                )
            );
        })
    );
    return = (main.mergeAttrs
        (main)
        ({
            nixPath = "${defaultFrom}";
            packages = packages;
            importMixin = (
                fileName : (builtins.import
                    (builtins.toPath
                        "${pathToThisFile}/../mixins/${fileName}"
                    )
                    ({
                        main = return;
                    })
                )
            );
            mergeMixins = (
                mixins : (
                    # this combines them into one big map ({}), which is done for any env vars they set
                    (main.foldl'
                        (curr: next: curr // next)
                        {}
                        mixins
                    )
                    
                    //
                    
                    # here's how all the normal attributes are merged
                    {
                        buildInputs = (main.concatLists
                            (main.map
                                (
                                    each: (  { buildInputs=[]; }   //   each  ).buildInputs
                                )
                                mixins
                            )
                        );
                        nativeBuildInputs = (main.concatLists
                            (main.map
                                (
                                    each: (  { nativeBuildInputs=[]; }   //   each  ).nativeBuildInputs
                                )
                                mixins
                            )
                        );
                        shellHook = (main.concatStringsSep "\n"
                            (main.map
                                (
                                    each: (  { shellHook=""; }   //   each  ).shellHook
                                )
                                mixins
                            )
                        );
                    }
                )
            );
            project = {
                buildInputs = buildInputs;
                nativeBuildInputs = nativeBuildInputs;
                shellHook = ''
                    # 
                    # find the fornix_core
                    # 
                    path_to_fornix_core=""
                    file_name="settings/fornix_core"
                    folder_to_look_in="$PWD"
                    while :
                    do
                        # check if file exists
                        if [ -f "$folder_to_look_in/$file_name" ]
                        then
                            path_to_fornix_core="$folder_to_look_in/$file_name"
                            break
                        else
                            if [ "$folder_to_look_in" = "/" ]
                            then
                                break
                            else
                                folder_to_look_in="$(dirname "$folder_to_look_in")"
                            fi
                        fi
                    done
                    if [ -z "$path_to_fornix_core" ]
                    then
                        #
                        # what to do if file never found
                        #
                        echo "Im part of parse_dependencies.nix, a script running with a pwd of:$PWD"
                        echo "Im looking for settings/fornix_core in a parent folder"
                        echo "Im exiting now because I wasnt able to find it"
                        echo "thats all the information I have"
                        exit
                    fi
                    export FORNIX_NEXT_RUN_DONT_DO_MANUAL_START="true"
                    . "$path_to_fornix_core"
                    
                    if [ "$FORNIX_DEBUG" = "true" ]; then
                        echo "starting: 'shellHook' inside the 'settings/extensions/nix/parse_dependencies.nix' file"
                    fi
                    
                    # ensure that the folder exists
                    mkdir -p "$(dirname "$__FORNIX_NIX_PATH_EXPORT_FILE")"
                    echo ${main.escapeShellArg (packagePathsAsJson)} > "$__FORNIX_NIX_PATH_EXPORT_FILE"
                    
                    if [ -n "$FORNIX_HOME" ]
                    then
                        # we don't want to give nix or other apps our home folder
                        if ! [ "$HOME" = "$FORNIX_HOME" ]
                        then
                            if [ "$FORNIX_DEBUG" = "true" ]; then
                                echo "replacing: HOME with FORNIX_HOME"
                            fi
                            mkdir -p "$FORNIX_HOME/.cache/"
                            ln -s "$HOME/.cache/nix/" "$FORNIX_HOME/.cache/" &>/dev/null
                            
                            # so make the home folder the same as the project folder
                            export HOME="$FORNIX_HOME"
                            # make it explicit which nixpkgs we're using
                            export NIX_PATH="nixpkgs=${defaultFrom}:."
                        fi
                    fi
                '';
            };
            
        })
    );
}).return