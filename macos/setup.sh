# install zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# copy my own .zshrc
cp ./.zshrc ~/.zshrc
source ~/.zshrc
 
# install brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> $HOME/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
 
# install required packages
brew update && \
    brew install neovim pyenv node coreutils ripgrep && \
    brew install --cask warp

# install Jetbrains Mono font
brew tap homebrew/cask-fonts
brew install --cask font-jetbrains-mono 

# install pyright
npm i -g pyright

# copy nvim dotfiles
cp -r ./nvim ~/.config/nvim/

# install vim-plug
sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'
 
# Install neovim packages with vim-plug
nvim --headless +PlugInstall +qall

# copy git config
cp ./git/.gitconfig ~/.gitconfig
