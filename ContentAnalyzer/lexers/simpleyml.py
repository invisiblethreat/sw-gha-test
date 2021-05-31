"""GitHead Lexer."""

import re
import attr
from ContentAnalyzer.lexers import LexerMatchBase

@attr.s(kw_only=True, slots=True)
class SimpleYamlKeyValue(LexerMatchBase):
    """SimpleYamlKeyValue."""

    key = attr.ib(default=None, type=str)
    value = attr.ib(default=None, type=str)

    _field_match_mappings = attr.ib(default={
        1: 'key',
        2: 'value',
    })

    _token_kind_mapping = attr.ib(default={
        'key': ['analyzer', 'Key'],
        'value': ['analyzer', 'Value'],
    })

    _token_kinds = attr.ib(default=[
        'analyzer.Key',
        'analyzer.Value',
    ])

    def consume_match(self, match):
        """Consume a regex match and populate self with it."""

        for match_number, field_name in self._field_match_mappings.items():
            start_pos = match.start(match_number)
            kind = self._get_field_to_kind(field_name)
            value = match.group(match_number).strip()

            match_tuple = self._make_token_tuple(start_pos, kind, value)

            setattr(self, field_name, match_tuple)

    # pylint: disable=no-member
    @property
    def tokens(self):
        """Spits out tokens from attributes."""

        props = [n for n in self.__slots__ if not n.startswith('_') and n != "__weakref__"]

        for n in props:
            token = getattr(self, n)
            yield token
    # pylint: enable=no-member

    @classmethod
    def from_dict(cls, data):
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
    def from_regex_match(cls, match):
        """Instantiate class from a regex match."""

        instance = cls()
        instance.consume_match(match)

        return instance

@attr.s(kw_only=True, slots=True)
class SimpleYamlLexer():
    """SimpleYamlLexer."""

    # pylint: disable=line-too-long
    # regex = attr.ib(default=r"^^\s+([a-zA-Z_\-\.]+): ([a-zA-Z0-9_\-\.\?\!\"\'\:\/\\\@\;\=\<\% \[\]\>\{\})\$]+[^ #])", type=str)
    # regex = attr.ib(default=r"^\s*(- )?([a-zA-Z_\-\.]+): ([a-zA-Z0-9_\-\.\?\!\"\'\:\/\\\@\\&;\=\<\% \[\]\*\>\{\})\$]+[^ #])", type=str)
    # regex = attr.ib(default=r"^\s*|#?\s*(?:- )?([a-zA-Z_\-\.]+): ([\w+_\-\.\?\!\"\'\:\/\\\@\\&;\=\<\% \[\]\*\>\{\})\$]+[^ #])")
    # regex = attr.ib(default=r"^(?:(?:\s*#?)\s*)(?:- )?([a-zA-Z_\-\.]+): ([\w+_\-\.\?\!\"\'\:\/\\\@\\&;\=\<\% \[\]\*\>\{\})\$]+[^ #])")
    regex = attr.ib(default=r"^(?:(?:\s*#?)\s*)(?:- )?([\w\-\.\[\]]+): ([\w+_\-\.,?!\"':\/@\\&;=<% \[\]*<>{}()$]+[^ #])")
    compiled_regex = attr.ib(default=None)
    # pylint: enable=line-too-long

    def __attrs_post_init__(self):

        self.compiled_regex = re.compile(self.regex, re.MULTILINE)

    def parse(self, text):
        """Parse text."""

        matches = re.finditer(self.compiled_regex, text)

        entries = [SimpleYamlKeyValue.from_regex_match(match) for match in matches]

        return entries

    def get_tokens_unprocessed(self, text):
        """Get tokens unprocessed."""

        entries = self.parse(text)
        for entry in entries:
            for prop in entry.tokens:
                yield prop

TEXT = """# ===================================================================
# Spring Boot configuration for the "dev" profile.
#
# This configuration overrides the application.yml file.
#
# More information on profiles: https://www.jhipster.tech/profiles/
# More information on configuration properties: https://www.jhipster.tech/common-application-properties/
# ===================================================================

# ===================================================================
# Standard Spring Boot properties.
# Full reference is available at:
# http://docs.spring.io/spring-boot/docs/current/reference/html/common-application-properties.html
# ===================================================================

logging:
    level:
        ROOT: DEBUG
        io.github.jhipster: DEBUG
        com.focusrunner.ezpill: DEBUG

spring:
    profiles:
        active: dev
        include: swagger
    devtools:
        restart:
            enabled: true
        livereload:
            enabled: false # we use Webpack dev server + BrowserSync for livereload
    jackson:
        serialization.indent_output: true
    cloud:
        consul:
            discovery:
               prefer-ip-address: true
            host: home.codestrong.biz
            port: 8500
    datasource:
        type: com.zaxxer.hikari.HikariDataSource
        url: jdbc:h2:file:./target/h2db/db/patientservice;DB_CLOSE_DELAY=-1
        username: patientService
        password:
    h2:
        console:
            enabled: false
    jpa:
        database-platform: io.github.jhipster.domain.util.FixedH2Dialect
        database: H2
        show-sql: true
        properties:
            hibernate.id.new_generator_mappings: true
            hibernate.cache.use_second_level_cache: true
            hibernate.cache.use_query_cache: false
            hibernate.generate_statistics: true
            hibernate.cache.region.factory_class: io.github.jhipster.config.jcache.BeanClassLoaderAwareJCacheRegionFactory
    liquibase:
        contexts: dev
    mail:
        host: localhost
        port: 25
        username:
        password:
    messages:
        cache-duration: PT1S # 1 second, see the ISO 8601 standard
    thymeleaf:
        cache: false
    zipkin: # Use the "zipkin" Maven profile to have the Spring Cloud Zipkin dependencies
        base-url: http://localhost:9411
        enabled: false
        locator:
            discovery:
                enabled: true

# ===================================================================
# To enable SSL, generate a certificate using:
# keytool -genkey -alias patientservice -storetype PKCS12 -keyalg RSA -keysize 2048 -keystore keystore.p12 -validity 3650
#
# You can also use Let's Encrypt:
# https://maximilian-boehm.com/hp2121/Create-a-Java-Keystore-JKS-from-Let-s-Encrypt-Certificates.htm
#
# Then, modify the server.ssl properties so your "server" configuration looks like:
#
# server:
#    port: 8443
#    ssl:
#        key-store: keystore.p12
#        key-store-password: <your-password>
#        key-store-type: PKCS12
#        key-alias: patientservice
# ===================================================================
server:
    port: 8203

# ===================================================================
# JHipster specific properties
#
# Full reference is available at: https://www.jhipster.tech/common-application-properties/
# ===================================================================

jhipster:
    http:
        version: V_1_1 # To use HTTP/2 you will need SSL support (see above the "server.ssl" configuration)
    cache: # Cache configuration
        ehcache: # Ehcache configuration
            time-to-live-seconds: 3600 # By default objects stay 1 hour in the cache
            max-entries: 100 # Number of objects in each cache entry
    # CORS is disabled by default on microservices, as you should access them through a gateway.
    # If you want to enable it, please uncomment the configuration below.
    # cors:
        # allowed-origins: "*"
        # allowed-methods: "*"
        # allowed-headers: "*"
        # exposed-headers: "Authorization,Link,X-Total-Count"
        # allow-credentials: true
        # max-age: 1800
    security:
        authentication:
            jwt:
                secret: my-secret-token-to-change-in-production
                # Token is valid 24 hours
                token-validity-in-seconds: 86400
                token-validity-in-seconds-for-remember-me: 2592000
    mail: # specific JHipster mail property, for standard properties see MailProperties
        from: patientService@localhost
        base-url: http://127.0.0.1:8203
    metrics: # DropWizard Metrics configuration, used by MetricsConfiguration
        jmx:
            enabled: true
        logs: # Reports Dropwizard metrics in the logs
            enabled: false
            report-frequency: 60 # in seconds
    logging:
        logstash: # Forward logs to logstash over a socket, used by LoggingConfiguration
            enabled: false
            host: localhost
            port: 5000
            queue-size: 512

# ===================================================================
# Application specific properties
# Add your own application properties here, see the ApplicationProperties class
# to have type-safe configuration, like in the JHipsterProperties above
#
# More documentation is available at:
# https://www.jhipster.tech/common-application-properties/
# ===================================================================

# application:
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: slack-autoarchive
  namespace: kube-services 
  labels:
    alert_type: "37-5-devops"
spec:
  schedule: "0 12 * * *"
  successfulJobsHistoryLimit: 1 
  failedJobsHistoryLimit: 1
  concurrencyPolicy: "Forbid"
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            alert_type: "37-5-devops"
        spec:
          automountServiceAccountToken: false
          containers:
          - name: slack-autoachive
            imagePullPolicy: Always 
            image: pasientskyhosting/slack-autoarchive
            env:
            - name: "SLACK_TOKEN"
              value: "xoxp-177954516944-177954517072-656555308452-1d67367d82ef3c75a2e348a409f214bc"
            - name: "DAYS_INACTIVE"
              value: "60" 
          restartPolicy: OnFailure
"""

DATABASE_YML1 = """# SQLite version 3.x
#   gem install sqlite3
#
#   Ensure the SQLite 3 gem is defined in your Gemfile
#   gem 'sqlite3'
#
default: &default
  adapter: postgresql
  encoding: unicode
  pool: 5
  timeout: 5000
  username: <%= ENV['POSTGRES_USER'] %>
  database: <%= ENV['POSTGRES_DB'] %>
  host: <%= ENV['POSTGRES_HOST'] %>
  port: <%= ENV['POSTGRES_PORT'] %>

development:
  <<: *default

# Warning: The database defined as "test" will be erased and
# re-generated from your development database when you run "rake".
# Do not set this db to the same as development or production.
test:
  <<: *default

production:
  <<: *default
"""

# # pylint: disable=unused-variable
# def main():
#     """Main."""

#     lexer = SimpleYamlLexer()
#     entries = list(lexer.get_tokens_unprocessed(DATABASE_YML1))

#     print("", end='')

# if __name__ == "__main__":
#     main()
