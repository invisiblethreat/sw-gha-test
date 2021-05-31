
text = """
PURPOSE_JAVA_MAVEN_POM_XML = "pom.xml"
PURPOSE_JAVA_MAVEN_POM_PROPERTIES = "pom.properties"
PURPOSE_JAVA_FRAMEWORK_SPRING_PROPERTIES = "application.properties"

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

PURPOSE_RUBY_GEMFILE = "Gemfile"
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
PURPOSE_VCS_GIT_HEAD = "HEAD"
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
"""

template = """
@register_and_prepare
def FUNCTION_NAME(file_):
    \"\"\"Classify file.

    Args:
        file_ (str or file object): Filename or file 'object'.
    
    Returns:
        bool: Whether or not file matches CONSTANT_NAME.
    \"\"\"

    if file_.name == "FILENAME":
        return CONSTANT_NAME

"""

template2 = """
  FUNCTION_NAME:
    name: FUNCTION_NAME
    description: TODO
    filename: FILENAME
    constant_name: CONSTANT_NAME
    constant_value: CONSTANT_VALUE
    lexer: LEXER
    how:
      - $ref: "#/Matches/exact_filename"
"""

def function_parser():
    global template

    template = "\n".join(template.split('\n')[1:-1])

    for n in text.split('\n'):
        if n == '':
            continue
        parts = n.split('_', 1)
        if '=' in n:
            constant_name, _ = n.split(' = ', 1)

        if parts[0] == "PURPOSE":
            function_name, filename = parts[1].split(' = ')
            function_name = function_name.lower()

            output = template.replace('FUNCTION_NAME', function_name)
            output = output.replace('"FILENAME"', filename)
            output = output.replace("CONSTANT_NAME", constant_name)

            print(output)

def yaml_parser():
    global template2

    template2 = "\n".join(template2.split('\n')[1:-1])

    for n in text.split('\n'):
        if n == '':
            continue
        parts = n.split('_', 1)
        if '=' in n:
            constant_name, _ = n.split(' = ', 1)

        if parts[0] == "PURPOSE":
            function_name, filename = parts[1].split(' = ')
            function_name = function_name.lower()

            output = template2.replace('FUNCTION_NAME', function_name)
            output = output.replace('FILENAME', filename.replace('"', ''))
            output = output.replace("CONSTANT_NAME", constant_name)
            output = output.replace('CONSTANT_VALUE', filename.replace('"', ''))

            print(output)
            print("")

yaml_parser()
