# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -n $SSH_CONNECTION ]]; then
  export EDITOR='vim'
else
  export EDITOR='nvim'
fi

ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"

if [ ! -d $ZINIT_HOME ]; then 
    mkdir -p "$(dirname $ZINIT_HOME)"
    git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
fi

# Load zinit
source "${ZINIT_HOME}/zinit.zsh"

# Add in zsh plugins
zinit light zsh-users/zsh-syntax-highlighting
zinit light zsh-users/zsh-completions
zinit light zsh-users/zsh-autosuggestions

# Add in snippets
zinit snippet OMZP::kubectl
zinit snippet OMZP::python

# Load completions
autoload -U compinit && compinit

# Keybindings
# alt+<- | alt+->
bindkey "^[[1;3C" forward-word
bindkey "^[[1;3D" backward-word
bindkey '^p' history-search-backward
bindkey '^n' history-search-forward
bindkey "^r" history-incremental-pattern-search-backward
bindkey '^F' autosuggest-accept

# History
HISTSIZE=5000
HISTFILE=~/.zsh_history
SAVEHIST=$HISTSIZE
HISTDUP=erase
setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

# Completion styling
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# Alias
alias ls="ls --color"
alias ll="ls -la"
alias d=docker
alias nv=nvim

alias g="git"

## kubernetes 
alias kcc="k config use-context"
alias kgc="k config get-contexts"
alias kcn="k config set-context --current --namespace"
alias kgp="k get pods"
alias kgn="k get namespaces"
alias kgd="k get deployments"


# Exports
export PATH="/opt/homebrew/opt/sqlite/bin:$PATH"
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
export PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
export PATH="/opt/homebrew/opt/gnu-sed/libexec/gnubin:$PATH"
export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"
export HOMEBREW_NO_AUTO_UPDATE=1
export BAT_PAGING='never'

# Java
JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-11.jdk/Contents/Home" 
JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-11.jdk/Contents/Home" 
[[ "$PATH" == *"$HOME/bin:"* ]] || export PATH="$HOME/bin:$PATH"

export PATH="/opt/homebrew/opt/swagger-codegen@2/bin:$PATH"


# Created by `pipx` on 2024-06-06 11:36:17
export PATH="$PATH:/Users/heorhi/.local/bin"

# Fixing terminal colors in tmux
export TERM=xterm-256color
export COLORTERM=truecolor

eval "$(zoxide init zsh)"

eval "$(starship init zsh)"
