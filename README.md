
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

**Ważne:** jeśli tworzysz README na GitHubie, nie wkładaj tych potrójnych backticków do backticków, które pokazują sam kod README — wtedy GitHub może je potraktować jako zakończenie bloku.
