# Linux installation

## Install neovim and python support
```bash
sudo apt update -y && \
sudo apt-get install neovim python3-neovim -y
```

## Install vim plug
```bash
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
```

## Copy config files to required position
```bash
cp -r dotfiles/nvim ~/.config/nvim/
```

## Install used plugins
Open nvim and use command :PlugInstall

## Install LSP servers (requires node, go)
```bash
npm install -g pyright
go install golang.org/x/tools/gopls@latest
```

# MacOS installation

## Install neovim and python support
```bash
brew install neovim
```

## Install vim plug
```bash
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
```

## Copy config files to required position
```bash
cp -r dotfiles/nvim ~/.config/nvim/
```

## Install used plugins
Open nvim and use command :PlugInstall

## Install pyright lsp server (requires node)
```bash
brew install node
npm install -g pyright
```
