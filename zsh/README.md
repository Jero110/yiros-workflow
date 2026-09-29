# Optional Zsh / Powerlevel10k themes

This folder is only for prompt styling. Skip it if you do not want to change your terminal UI.

Variants:

- `p10k-simple-purple-git.zsh`: minimal prompt with soft purple git info.
- `p10k-orange-white.zsh`: orange + white block prompt.

Install one manually:

```sh
cp zsh/p10k-simple-purple-git.zsh ~/.p10k.zsh
exec zsh
```

or:

```sh
cp zsh/p10k-orange-white.zsh ~/.p10k.zsh
exec zsh
```

This repo does not ship `.zshrc` or `.zprofile`. If your shell does not already load Powerlevel10k, configure that separately.
