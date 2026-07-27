
W README wyrenderuje się wtedy jako:

> **How to add repository**
>
> 1. Open `/etc/pacman.conf` and add at the end of the file:
>
> ```ini
> [arcos-repo]
> SigLevel = Never
> Server = https://zcharka.github.io/arcos-repo/$arch
> ```
>
> 2. Synchronize the repository database:
>
> ```bash
> sudo pacman -Sy
> ```
