"""SimpleBash Lexer."""

import re
from typing import Dict, Iterable, List, Tuple

import attr

from ContentAnalyzer.lexers import LexerMatchBase


@attr.s(kw_only=True, slots=True)
class SimpleBashKeyValue(LexerMatchBase):
    """SimpleBashKeyValue.

    Args:

        key (Tuple[int, str, str]): Tuple of key start position, name, value.
        value (Tuple[int, str, str]): Tuple of balue start position, name, value.
    """


    key: Tuple[int, str, str] = attr.ib(default=None)
    value: Tuple[int, str, str] = attr.ib(default=None)


    _field_match_mappings = attr.ib(default={
        1: 'key',
        2: 'value',
        3: 'value',
        4: 'value',
        5: 'value',
    }, repr=False)

    _token_kind_mapping = attr.ib(default={
        'key': ['analyzer', 'Key'],
        'value': ['analyzer', 'Value'],
    }, repr=False)

    _token_kinds = attr.ib(default=[
        'analyzer.Key',
        'analyzer.Value',
    ], repr=False)


    # pylint: disable=try-except-raise
    def consume_match(self, match: 're.MATCH') -> None:
        """Consume a regex match and populate self with it."""

        for match_number, field_name in [(1, 'key'), (2, 'value')]:
            start_pos = match.start(match_number)
            kind = self._token_kind_mapping[field_name]
            value = match.group(match_number)
            if value is None and field_name == "value":
                i = 1
                while True:
                    try:
                        _ = self._field_match_mappings[match_number + i]
                    except KeyError:
                        # Give up
                        raise
                    value = match.group(match_number + i)
                    if value is not None:
                        # Found a match!
                        start_pos = match.start(match_number + i)
                        break
                    i += 1

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)
    # pylint: enable=try-except-raise


    # pylint: disable=no-member
    @property
    def tokens(self) -> Tuple[int, str, str]:
        """Spits out tokens from attributes.

        Returns:

            Iterable: Iterable containing Tuple[int, str, str] of position, token kind, token value.
        """

        props = [n for n in self.__slots__ if not n.startswith('_') and n != "__weakref__"]

        for n in props:
            token = getattr(self, n)
            yield token
    # pylint: enable=no-member


    @classmethod
    def from_dict(cls, data: Dict) -> 'SimpleBashKeyValue':
        """Instantiate class from a dict."""

        instance = cls()
        for k, v in data.items():
            try:
                setattr(instance, k, v)
            except AttributeError:
                # We don't have this attribute so ignore
                pass

        return instance


    @classmethod
    def from_regex_match(cls, match: 're.MATCH') -> 'SimpleBashKeyValue':
        """Instantiate class from a regex match."""

        instance = cls()
        instance.consume_match(match)

        return instance


@attr.s(kw_only=True, slots=True)
class SimpleBashLexer():
    """SimpleBashLexer."""

    # pylint: disable=line-too-long
    # regex = attr.ib(default=r"^\s*(\w+) ?= ?([\S ]+)", type=str)
    # This regex will pick up variables with ${variables} in them and perhaps less processor intensive
    # as " ? = ?" has been redone to "="
    regex = attr.ib(default=r"^[\s#]*(?:(?:export) )?([\w\{\}\$]+)=(?:'([\S ]+)'|\"([\S ]+)\"|`([\S ]+)`|([\S ]+))", type=str)
    compiled_regex = attr.ib(default=None)
    # pylint: enable=line-too-long

    def __attrs_post_init__(self):

        self.compiled_regex = re.compile(self.regex, re.MULTILINE)


    def parse(self, text: str) -> List[SimpleBashKeyValue]:
        """Parse text.

        Args:

            text (str): Text to parse.

        Returns:

            List[SimpleBashKeyValue]: List of SimpleBashKeyValue tokens.
        """

        matches = re.finditer(self.compiled_regex, text)

        entries = [SimpleBashKeyValue.from_regex_match(match) for match in matches]

        return entries


    def get_tokens_unprocessed(self, text: str) -> Iterable:
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop


# TODO: Update example
TEXT = """RESTAPI_IP = str(os.environ.get('RGW_CIVETWEB_HOST', failobj='127.0.0.1'))
RESTAPI_PORT = int(os.environ.get('RGW_CIVETWEB_PORT', failobj=9004))
S3_URL = RESTAPI_IP + ":" + str(RESTAPI_PORT)
ACCESS_KEY = 'ceph'
SECRET_KEY = 'ceph123'
BUCKET_NAME = 'druid-deep-store'
    BUCKET_NAME = 'druid-deep-store'
BUCKET_NAME='druid-deep-store'
"""

# pylint: disable=anomalous-backslash-in-string
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
# pylint: enable=anomalous-backslash-in-string

# pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = SimpleBashLexer()
#     entries = list(lexer.get_tokens_unprocessed(TEXT2))

#     print("", end='')

# if __name__ == "__main__":
#     main()
