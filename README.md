# ArcOS-repo
#repository for my distribution - ArcOS

**how to add repository**

1. Open pacman.conf '/etc/pacman.conf' and add in end of file

'[arcos-repo]
SigLevel = Never
Server = https://zcharka.github.io/arcos-repo/$arch'

2. Synchronize all of repository - use 'sudo pacman -Sy' to download the ArcOS-repo
