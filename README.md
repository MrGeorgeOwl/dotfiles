### Linux installation

# Install neovim and python support
sudo apt update -y && \
sudo apt-get install neovim python3-neovim -y

# Install vim plug
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'


# Copy config files to required position
cp -r dotfiles/nvim ~/.config/nvim/

# Install used plugins
Open nvim and use command :PlugInstall

# Install pyright lsp server (requires node)
npm install -g pyright
