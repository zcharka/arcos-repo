EN:

**How to add repository**

> 1. Open `/etc/pacman.conf` e.g `nano /etc/pacman.conf` and add at the end of the file:
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

PL:

**Jak dodać repozytorium**

> 1. Otwórz `/etc/pacman.conf` np. `nano /etc/pacman.conf` i dodaj to na końcu pliku:
>
> ```ini
> [arcos-repo]
> SigLevel = Never
> Server = https://zcharka.github.io/arcos-repo/$arch
> ```
>
> 2. Zsynchrfonizuj bazy repozytorii:
>
> ```bash
> sudo pacman -Sy
> ```
