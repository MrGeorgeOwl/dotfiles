export PATH="/home/owl/.local/bin:$PATH"

# history
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_IGNORE_SPACE
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS
setopt SHARE_HISTORY

# load search functionality
autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search

# make widgets from newly load functions
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search

# bind search history keys
bindkey '^P' up-line-or-beginning-search
bindkey '^N' down-line-or-beginning-search

# bind incremental search keys
bindkey '^R' history-incremental-search-backward
# end history

bindkey -e

# The following lines were added by compinstall
zstyle :compinstall filename '/home/owl/.zshrc'

autoload -Uz compinit
compinit
# End of lines added by compinstall

eval "$(starship init zsh)"
eval "$(zoxide init zsh)"

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
if [ -f ~/.zsh_aliases ]; then
    . ~/.zsh_aliases
fi

. "$HOME/.cargo/env"

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
