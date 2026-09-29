# Powerlevel10k instant prompt. Keep this near the top.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Oh My Zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git)
source "$ZSH/oh-my-zsh.sh"

# Conda
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$(/opt/homebrew/Caskroom/miniconda/base/bin/conda shell.zsh hook 2> /dev/null)"
if [ $? -eq 0 ]; then
  eval "$__conda_setup"
else
  if [ -f "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]; then
    . "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
  else
    export PATH="/opt/homebrew/Caskroom/miniconda/base/bin:$PATH"
  fi
fi
unset __conda_setup
# <<< conda initialize <<<

# PATH / env needed by local tools
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
[ -d "$HOME/.antigravity/antigravity/bin" ] && export PATH="$HOME/.antigravity/antigravity/bin:$PATH"
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export NODE_EXTRA_CA_CERTS=/etc/ssl/cert.pem
export CLOUDSDK_PYTHON=/opt/homebrew/Caskroom/miniconda/base/envs/gcloud/bin/python

# Claude Code wrapper
[[ -f ~/.config/zsh/cc.zsh ]] && source ~/.config/zsh/cc.zsh
cs() { cc "$@"; }

# Claude Monitor
claude_monitor() {
  local monitor_dir="${CLAUDE_MONITOR_DIR:-$HOME/ClaudeMonitor}"

  lsof -ti tcp:7337 2>/dev/null | xargs kill -9 2>/dev/null
  sleep 0.3

  trap 'echo "\nStopping monitor…"; lsof -ti tcp:7337 2>/dev/null | xargs kill -9 2>/dev/null; trap - INT QUIT; return 0' INT QUIT

  echo "Starting claude monitor… (Ctrl+C to stop)"
  python3 "$monitor_dir/claude-meta.py" &
  sleep 1 && open "http://localhost:7337" &
  local server_pid=$!

  wait $server_pid
  trap - INT QUIT
}

# Powerlevel10k config
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
