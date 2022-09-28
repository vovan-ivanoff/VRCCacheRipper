# VRCCacheRipper
Script that extracts avatars and worlds from vrc cache

ru documentation: [a relative link](other_file.md)
# Getting Started
- Download and unpack AssetRipper from here: `https://github.com/AssetRipper/AssetRipper`
- Download this script and place it into AssetRipper folder(where AssetRipper.exe is located)
- run `pip install vrchatapi`
- Done!

# Usage
To use simply use this script open command line and run `python script.py -o [output directory] --nonaming` Please note, that **output directory should exist!**

If you want more advanced usage and avatar naming use `-u [username] -p [password] ` instead of `--nonaming`
where `username` and `password` is any account(even newly created) vrchat credentials (used to VRChat Api calls for naming) **2fa is not currently supported! **


Cmdline args and their description:
- `-s [SIZE] ` maximum size of vrchat avatar in MB
- `-i [path to vrchat cache] ` path to vrchat cache, in case when auto detection does not work (Cache-Windows Player directory)
- `-mins [SIZE] ` minimum size of avatar in MB
- `-asr [path to AssetRipper.exe] ` path to AssetRipper.exe when installed into different directory
- `-v` verbose output of assetripper
- and of course `-h` prints help
