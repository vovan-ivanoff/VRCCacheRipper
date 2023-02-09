# VRCCacheRipper
Script that extracts avatars and worlds from vrc cache
also supports classification by model (rex, nardo, wicker, etc...)

Русская документация: [Тык](Rudoc.md)
# Getting Started
- Run `insatll.bat` this batch file automatically downloads and installs everything needed 
- Done!

# Usage
To use simply use this script open command line and run `ripper.bat -o [output directory] --nonaming` Please note, that ***output directory should exist!***

If you want more advanced usage and avatar naming use `-u [username] -p [password] ` instead of `--nonaming`
where `username` and `password` is any account(even newly created) vrchat credentials (used to VRChat Api calls for naming) **2fa is not currently supported! **


Cmdline args and their description:
- `-s [SIZE] ` maximum size of vrchat avatar in MB
- `-i [path to vrchat cache] ` path to vrchat cache, in case when auto detection does not work (Cache-Windows Player directory)
- `-mins [SIZE] ` minimum size of avatar in MB
- `-asr [path to AssetRipper.exe] ` path to AssetRipper.exe when installed into different directory
- `-j` number of unpacking threads
- `-clsf` does not unpack, only classify
- and of course `-h` prints help
