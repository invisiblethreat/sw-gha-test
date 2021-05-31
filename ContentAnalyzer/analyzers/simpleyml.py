"""Simple Yaml analyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair

class SimpleYamlAnalyzer(Document):
    """SimpleYamlAnalyzer"""

    # pylint: disable=unused-argument
    def analyze(self, content):
        """Analyze content.

        Args:
            content (str): Content to analyze.
        """

        self.set_lexer("SimpleYamlLexer")

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

default: &default
  username: <%= ENV['POSTGRES_USER'] %>
  database: <%= ENV['POSTGRES_DB'] %>
  host: <%= ENV['POSTGRES_HOST'] %>
  port: <%= ENV['POSTGRES_PORT'] %>

# ===================================================================
# Application specific properties
# Add your own application properties here, see the ApplicationProperties class
# to have type-safe configuration, like in the JHipsterProperties above
#
# More documentation is available at:
# https://www.jhipster.tech/common-application-properties/
# ===================================================================

# This role starts a nginx component
- name: ensure nginx config directory exists
  file:
    path: "{{ nginx.confdir }}"
    state: directory

# application:
    org.springframework.security: DEBUG
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

def main():
    """Main."""

    doc = SimpleYamlAnalyzer()
    doc.analyze(TEXT)

    # kinds = doc.get_token_kinds()
    # print("expected = [")
    # for n in kinds:
    #     print("    '%s'," % n)
    # print("]")

    # print("expected = {")
    # for kind in kinds: 
    #     print("    '%s': %s," % (kind, len(list(doc.get_tokens(kind=kind))))) 
    # print("}")

    for n in doc.get_kvps():
        print(n.get_key_start_pos())

    print("breakpoint")

if __name__ == "__main__":
    main()
