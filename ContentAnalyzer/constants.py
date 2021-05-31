"""Constants."""

SOURCE_CODE = {
    'python': 'python',
    'javascript': 'javascript',
    'typescript': 'typescript',
    'jsx': 'jsx',
    'html': 'html',
    'css': 'css',
    'perl': 'perl',
    'php': 'php',
    'shell': 'shell',
    'awk': 'awk',
    'lua': 'lua',
    'r': 'r',
    'ruby': 'ruby',
    'scala': 'scala',
    'cmake': 'cmake',
    'coffeescript': 'coffeescript',
    'coldfusion': 'coldfusion',
    'lisp': 'lisp',
    'erlang': 'erlang',
    'f#': 'f#',
    'fortran': 'fortran',
    'go': 'go',
    'haskell': 'haskell',
    'kotlin': 'kotlin',
    'latex': 'latex',
    'less': 'less',
    'make': 'make',
    'pascal': 'pascal',
    'rust': 'rust',
    'sql': 'sql',
    'tcl': 'tcl',
    'swift': 'swift',
    'tcsh': 'tcsh',
    'visual basic': 'visual basic',
    'yaml': 'yaml',
    'd': 'd',
    'java': 'java',
    'c': 'c',
    'c++': 'c++',
    'c#': 'c#',
    'objective-c': 'objective-c',
    'assembly': 'assembly',
    'verilog': 'verilog',
    'vhdl': 'vhdl',
    'protobuf': 'protbuf',
}

CONTENT_PYTHON = "python"

CONTENT_JAVA = "java"
CONTENT_SCALA = "scala"
CONTENT_KOTLIN = "kotlin"
CONTENT_JAVASCRIPT = "javascript"
CONTENT_TYPESCRIPT = "typescript"
CONTENT_JSX = "jsx"
CONTENT_COFFEESCRIPT = "coffeescript"

CONTENT_HTML = "html"
CONTENT_CSS = "css"

CONTENT_PERL = "perl"
CONTENT_PHP = "php"
CONTENT_R = "r"
CONTENT_RUBY = "ruby"
CONTENT_LUA = "lua"
CONTENT_COLDFUSION = "coldfusion"
CONTENT_LISP = "lisp"
CONTENT_ERLANG = "erlang"
CONTENT_FSHARP = "fsharp"
CONTENT_FORTRAN = "fortran"
CONTENT_GO = "go"
CONTENT_HASKELL = "haskell"
CONTENT_PASCAL = "pascal"
CONTENT_RUST = "rust"
CONTENT_SWIFT = "swift"
CONTENT_VISUAL_BASIC = "visual basic"
CONTENT_D = "d"

CONTENT_C = "c"
CONTENT_CPP = "cpp"
CONTENT_CSHARP = "csharp"
CONTENT_OBJECTIVE_C = "objective-c"

CONTENT_SHELL = "shell"
CONTENT_BASH = "bash"
CONTENT_SH = "sh"
CONTENT_CSH = "csh"
CONTENT_TCSH = "tcsh"
CONTENT_FISH = "fish"

CONTENT_AWK = "awk"
CONTENT_MAKE = "make"
CONTENT_CMAKE = "cmake"
CONTENT_LESS = "less"

CONTENT_LATEX = "latex"
CONTENT_TCL = "tcl"

CONTENT_SQL = "sql"
CONTENT_CYPHER = "cypher"
CONTENT_MYSQL = "mysql"
CONTENT_POSTGRES = "postgres"
CONTENT_SQLITE = "sqlite"

CONTENT_ASSEMBLY = "assembly"
CONTENT_VERILOG = "verilog"
CONTENT_VHDL = "vhdl"

CONTENT_PROTOBUF = "proto"

CONTENT_XML = "xml"
CONTENT_JSON = "json"
CONTENT_YAML = "yaml"
CONTENT_MARKDOWN = "markdown"
CONTENT_RST = "rst"
CONTENT_DOCKERFILE = "dockerfile"

PURPOSE_JAVA_MAVEN_POM_XML = "pom.xml"
PURPOSE_JAVA_MAVEN_POM_PROPERTIES = "pom.properties"
PURPOSE_JAVA_FRAMEWORK_SPRING_PROPERTIES = "application.properties"
PURPOSE_JAVA_FRAMEWORK_SPRING_BOOTSTRAP = "bootstrap.yml"

PURPOSE_JAVASCRIPT_PACKAGE = "package.json"
PURPOSE_JAVASCRIPT_PACKAGE_LOCK = "package-lock.json"
PURPOSE_JAVASCRIPT_YAPM_PACKAGE_JSON = "package.json5"
PURPOSE_JAVASCRIPT_YAPM_PACKAGE_YAML = "package.yaml"
PURPOSE_JAVASCRIPT_NPM_IGNORE = ".npmignore"
PURPOSE_JAVASCRIPT_NPM_SHRINKWRAP = "npm-shrinkwrap.json"
PURPOSE_JAVASCRIPT_NPM_UPDATE_NOTIFIER = "update-notifier-npm.json"
PURPOSE_JAVASCRIPT_NPM_CLI_METRICS = "anonymous-cli-metrics.json"
PURPOSE_JAVASCRIPT_YARN_INTEGRITY = ".yarn-integrity"
PURPOSE_JAVASCRIPT_YARN_LOCK = "yarn.lock"
PURPOSE_JAVASCRIPT_BOWER_DEPENDENCIES = "bower.json"
PURPOSE_JAVASCRIPT_JSHINT_CONFIG = ".jshintrc"
PURPOSE_JAVASCRIPT_TYPESCRIPT_LINT_CONFIG = "tslint.json"
PURPOSE_JAVASCRIPT_COFFEESCRIPT_LINT_CONFIG = "coffeelint.json"
PURPOSE_JAVASCRIPT_COFFEESCRIPT_BUILD_CONFIG = "Cakefile"
PURPOSE_JAVASCRIPT_WEBPACK_CONFIG = "webpack.config.js"
PURPOSE_JAVASCRIPT_BABEL_CONFIG = ".babelrc"
PURPOSE_JAVASCRIPT_GROWL_TAGS = ".tags"
PURPOSE_JAVASCRIPT_NIGHTWATCH_CONFIG = "nightwatch.json"
PURPOSE_JAVASCRIPT_JAKEJS_BUILD_CONFIG = "Jakefile"

PURPOSE_RUBY_GEMFILE = "Gemfile"
PURPOSE_RUBY_GEMFILE_LOCK = "Gemfile.lock"
PURPOSE_RUBY_RAKE_TASKS = ".rakeTasks"
# Could be a custom (non-standard) log
PURPOSE_RUBY_DEVELOPMENT_LOG = "development.log"

PURPOSE_PYTHON_PACKAGE_DEPENDENCIES = "requirements.txt"
PURPOSE_PYTHON_PACKAGE_SETUP = "setup.py"

PURPOSE_CI_TRAVIS = ".travis.yml"
PURPOSE_CI_GITLAB = ".gitlab-ci.yml"
PURPOSE_CI_DRONE = ".drone.yml"
PURPOSE_CI_APPVEYOR = "appveyor.yml"

PURPOSE_VCS_GIT_CONFIG = "config"
PURPOSE_VCS_GIT_LOG = "HEAD"
PURPOSE_VCS_GIT_IGNORE = ".gitignore"
PURPOSE_VCS_GIT_MODULES = ".gitmodules"
PURPOSE_VCS_GIT_ATTRIBUTES = ".gitattributes"
PURPOSE_VCS_GIT_DIR = ".git"

PURPOSE_UNIX_AUTH_PASSWD = "passwd"
PURPOSE_UNIX_AUTH_SHADOW = "shadow"
PURPOSE_UNIX_AUTH_GROUP = "group"
PURPOSE_UNIX_AUTH_GSHADOW = "gshadow"

PURPOSE_UNIX_LOG_MESSAGES = "messages"
PURPOSE_UNIX_LOG_SYSLOG = "syslog"
PURPOSE_UNIX_LOG_AUDIT = "audit.log"
PURPOSE_UNIX_LOG_BOOTSTRAP = "bootstrap.log"

PURPOSE_UNIX_PKGMGMT_DPKG_LOG = "dpkg.log"
PURPOSE_UNIX_PKGMGMT_APT_HISTORY_LOG = "history.log"
PURPOSE_UNIX_PKGMGMT_APT_TERM_LOG = "term.log"
PURPOSE_UNIX_PKGMGMT_YUM_CONFIG_MAIN = "config-main"
PURPOSE_UNIX_PKGMGMT_YUM_CONFIG_REPO = "config-repo"
PURPOSE_UNIX_PKGMGMT_YUM_REPOMD = "repomd.xml"
PURPOSE_UNIX_PKGMGMT_YUM_LOG = "yum.log"
PURPOSE_UNIX_PKGMGMT_YUM_MIRRORLIST = "mirrorlist.txt"
PURPOSE_UNIX_PKGMGMT_YUM_HISTORY_SQL = "history-.sqlite"
PURPOSE_UNIX_PKGMGMT_YUM_SAVED_TX = "saved_tx"
PURPOSE_UNIX_PKGMGMT_YUM_PRIMARY_DB = "primary_db.sqlite"

PURPOSE_MACOS_METADATA_DIRECTORY = ".DS_Store"

PURPOSE_SHELL_BASH_HISTORY = ".bash_history"
PURPOSE_SHELL_BASH_CONFIG = ".bashrc"
PURPOSE_SHELL_GENERIC_HISTORY = ".history"
PURPOSE_SHELL_ENVIRONMENT = ".env"

PURPOSE_SSH_PRIVATE_KEY = "id_rsa"

PURPOSE_DOCKER_DOCKERFILE = "Dockerfile"
PURPOSE_DOCKER_ENTRYPOINT = "docker-entrypoint.sh"
PURPOSE_DOCKER_IGNORE = ".dockerignore"
PURPOSE_DOCKER_COMPOSE = "docker-compose.yml"

PURPOSE_PROGRAM_WGET_CONFIG = "wgetrc"

PURPOSE_PROGRAM_IDEA_CONFIG_WORKSPACE = "workspace.xml"
PURPOSE_PROGRAM_IDEA_CONFIG_VCS = "vcs.xml"
PURPOSE_PROGRAM_IDEA_WATCHER_TASKS = "watcherTasks.xml"
PURPOSE_PROGRAM_IDEA_DB_NAVIGATOR = "dbnavigator.xml"

PURPOSE_PROGRAM_SUBLIME_WORKSPACE = ".sublime-workspace"

PURPOSE_PROGRAM_VIM_RECOVERY = ".swp"

PURPOSE_PROGRAM_MYSQL_CONFIG = "my.cnf"

PURPOSE_PROGRAM_ANACONDA_JOURNAL_LOG = "journal.log"

PURPOSE_PROGRAM_RABBITMQ_CONFIG = "rabbitmq.config"

