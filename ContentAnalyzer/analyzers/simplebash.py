"""Simple Bash analyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair

class SimpleBashAnalyzer(Document):
    """SimpleBashAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        self.set_lexer("SimpleBashLexer")

        self.parse(content)

        left_side = None
        right_side = None
        for token in self.all_tokens:
            if token.kind == "analyzer.Key":
                left_side = token
            elif token.kind == "analyzer.Value":
                right_side = token
                kv_pair = KeyValuePair.from_tokens(left_side, right_side)
                self.kvps.append(kv_pair)
                left_side = None
                right_side = None
            else:
                raise ValueError("Unknown token kind '%s'" % token.kind)

    # pylint: enable=unused-argument

# TODO: Update example
TEXT = """FILENAME=$1
TOKEN=(`curl http://some-url.com`)
"""

TEXT2 = """setopt nonomatch

HISTFILE="$HOME/.zhistory"
HISTSIZE=100000
SAVEHIST=100000

PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/X11/bin
export PATH
export PATH=$PATH:/Users/HIROAKI/android-sdks/platform-tools
export ANDROID_HOME=/Users/HIROAKI/android-sdks
export EDITOR=vim

export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init -)"
export CC=/usr/bin/gcc

autoload -U compinit
compinit

setopt append_history
setopt hist_ignore_space
setopt nobeep
setopt prompt_subst
setopt extended_glob
setopt no_flow_control
setopt print_eight_bit
setopt auto_cd
setopt autopushd
setopt pushd_ignore_dups
setopt auto_menu
setopt correct
setopt ignore_eof

#zstyle ':completion:*' verbose yes
#zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'
zstyle ':completion:*:default' list-colors ''
#zstyle ':completion:*:default' menu select=1
#zstyle ':completion:*:descriptions' format '%B%d%b'
#zstyle ':completion:*:messages' format '%d'
#zstyle ':completion:*:warnings' format 'No matches for: %d'
#zstyle ':completion:*' group-name ''

PROMPT=$'%{\e[34m%}%n@%m%{\e[m%}%{\e[m%} $ '
RPROMPT=$'%{\e[32m%}[%~]%{\e[m%}'

stty -istrip
bindkey -e

autoload history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
bindkey '^p' history-beginning-search-backward-end
bindkey '^n' history-beginning-search-forward-end

alias history='fc -Dil'
alias his='history | tail'

alias ls='ls -G -AF'
alias ll='ls -al'
alias l='ls -al'
alias rm='nocorrect rm -i'
alias cp='cp -ip'
alias mv='mv -i'
alias git='nocorrect git'
alias r='rails'

# original
alias st='screen -t'

# Docker
alias dc='docker container'
alias di='docker image'
alias dv='docker volume'
alias dn='docker network'

alias d-c='docker-compose'

# Add environment variable COCOS_CONSOLE_ROOT for cocos2d-x
export COCOS_CONSOLE_ROOT=/Users/HIROAKI/opt/cocos2d-x-3.4/tools/cocos2d-console/bin
export PATH=$COCOS_CONSOLE_ROOT:$PATH

# Add environment variable COCOS_TEMPLATES_ROOT for cocos2d-x
export COCOS_TEMPLATES_ROOT=/Users/HIROAKI/opt/cocos2d-x-3.4/templates
export PATH=$COCOS_TEMPLATES_ROOT:$PATH
export PATH="$HOME/.rbenv/bin:$PATH"
eval "$(rbenv init -)"

set runtimepath+=/Applications/qfixhowm-master

export DEVISE_SECRET_KEY='09e64c732ad2079a296b3fd670bac4179d8115e3750b9de1def3fcc03bbf2890b575c8ce5bf0cce551e4c57c4c02cfba0ad78931f7ac525fcaca485b79c62361'
export SECRET_KEY_BASE='adc622c224caa8d60966967109da933e1e855beb9e1c4e0084e04434e058387a439d47f5d58444f6c3a5cd8df34c7b2b272c4a1bada6f5ea7e46c24fe6e9c6d2'
export PATH=$PATH:/Users/hiroaki/.nodebrew/current/bin
export SLACK_TOKEN=xoxp-480290906294-478890564626-493193214482-ff1857265064ba34659c3c09c3fa9fc1

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/hiroaki/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/hiroaki/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/hiroaki/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/hiroaki/google-cloud-sdk/completion.zsh.inc'; fi

# MySQL
export PATH="/usr/local/opt/mysql@5.7/bin:$PATH"
export DYLD_LIBRARY_PATH="/usr/local/opt/mysql@5.7/:$DYLD_LIBRARY_PATH"

# BriendCoinAPI
export SLACK_TOKEN='xoxp-480290906294-478890564626-498177603287-732c8a87dec3b7d21a2e8411f5008a66'
export SLACK_TOKEN_TE48JSN8N='xoxb-480290906294-500664234550-4JKA8Uy9xyShZHcsKbsdEAy4' # bod-demo
export SLACK_TOKEN_TCNV9GC94='xoxb-430995556310-509962609217-7GGXWoYlQ58VjXlCEaIAHrJV' # らくこい
export SLACK_TOKEN_TGEK6T2JD='xoxb-558652920625-559895925988-BnpnzSNpEcAzm5B1hU3pWnkb' # Social Quest
export SLACK_TOKEN_TCMSB6E6M='xoxb-429895218225-573645773683-9x9j3mySqQLvGeycnX8mdDOp' # すいみん
export DATABASE_URL='postgres://ouoalwgcwjarsz:71dbf856416c2671109e1fabdad5a8070becb71754c2c138c2ccfe4714e329b3@ec2-54-83-23-121.compute-1.amazonaws.com:5432/de7j2s0f1bf3l9'


export PATH="/usr/local/opt/openssl/bin:$PATH"
#export HOMEBREW_FORCE_BREWED_CURL=1

# GO
#export GOPATH=$HOME/go/package:$HOME/go/workspace
#export PATH=$HOME/go/package/bin:$HOME/go/workspace/bin:$PATH
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"

# tabtab source for serverless package
# uninstall by removing these lines or running `tabtab uninstall serverless`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/serverless.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/serverless.zsh
# tabtab source for sls package
# uninstall by removing these lines or running `tabtab uninstall sls`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/sls.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/sls.zsh
# tabtab source for slss package
# uninstall by removing these lines or running `tabtab uninstall slss`
[[ -f /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/slss.zsh ]] && . /usr/local/lib/node_modules/serverless/node_modules/tabtab/.completions/slss.zsh

# Python
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(direnv hook bash)"

export LANG=ja_JP.UTF-8

## peco ###################################3
function select-history() {
    local tac
    if which tac > /dev/null; then
        tac="tac"
    else
        tac="tail -r"
    fi
    BUFFER=$(fc -l -n 1 | eval $tac | peco --query "$LBUFFER")
    CURSOR=$#BUFFER
    zle -R -c
}
zle -N select-history
bindkey '^r' select-history
## peco ###################################3

#!/bin/bash
set -e

#################
### Do checks ###
#################
if [ -z "$CUSTOM_TAG" ] || [ -z "$SERVICE" ] || [ -z "$CLUSTER_KEY" ] ; then
    echo "Error: Make sure you are providing all necessary env vars to run.sh!"
    exit 1
fi

####################
### Get env vars ###
####################
export PUSH_IMAGES="no"
export TEMPLATE_ONLY=${TEMPLATE_ONLY:-"no"}
export CLUSTER_KEY=${CLUSTER_KEY:-""}
export URI_NAMESPACE=${URI_NAMESPACE:-"gcr.io/nutanix-epoch-dev"}
export PRODUCT_FLAVOR=Pro
service_str=$(echo $SERVICE | tr a-z A-Z | tr '-' '_')
export EPOCH_${service_str}_TAG="$CUSTOM_TAG"
export PYTHONPATH="./infra/jenkins/epoch-build-common"
export NAMESPACE=${NAMESPACE:-"epoch"}

if [ -n "$EPOCH_COMMIT_HASH" ] ; then
    RELEASE="$EPOCH_COMMIT_HASH"
else
    RELEASE="$CUSTOM_TAG"
fi

######################
### Clone k8s repo ###
######################
./kubernetes/clone.sh

##############################
### Build charts container ###
##############################
python ./infra/jenkins/build-images/build-push-charts-container.py

############################
### Run template/upgrade ###
############################
# TODO: NEED THE DEFAULT
RELEASE=${RELEASE} \
ACTION="template" \
ENV=${ENV:-"dev"} \
CLUSTER_KEY=${CLUSTER_KEY} \
NAMESPACE=${NAMESPACE} ./kubernetes/epoch-deploy/app-setup.sh

#####################################
### Apply the changes via kubectl ###
#####################################
if [ "$TEMPLATE_ONLY" = "no" ] ; then
    kubectl apply -f ./kubernetes/epoch-deploy/manifests/epoch/charts/$SERVICE/templates
fi
"""

def main():
    """Main."""

    doc = SimpleBashAnalyzer()
    doc.analyze(TEXT2)

    # kinds = doc.get_token_kinds()
    # print("expected = [")
    # for n in kinds:
    #     print("    '%s'," % n)
    # print("]")

    # print("expected = {")
    # for kind in kinds: 
    #     print("    '%s': %s," % (kind, len(list(doc.get_tokens(kind=kind))))) 
    # print("}")

    # for n in doc.get_kvps():
    #     print(n)

    kvps = doc.get_kvps()

    print("breakpoint")

if __name__ == "__main__":
    main()
