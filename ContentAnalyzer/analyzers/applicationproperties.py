"""ApplicationPropertiesAnalyzer."""

from ContentAnalyzer.lexers import Document, KeyValuePair

class ApplicationPropertiesAnalyzer(Document):
    """ApplicationPropertiesAnalyzer."""

    # pylint: disable=unused-argument
    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:

            content (str): Content to analyze.
        """

        self.set_lexer("ApplicationPropertiesLexer")

        self.parse(content)

        left_side = None
        right_side = None
        for token in self.all_tokens:
            if token.kind == "analyzer.Key":
                if token.value is None:
                    continue
                left_side = token
            elif token.kind == "analyzer.Value":
                right_side = token
                kv_pair = KeyValuePair.from_tokens(left_side, right_side)
                self.kvps.append(kv_pair)
                left_side = None
                right_side = None
            else:
                raise ValueError(f"Unknown token kind '{token.kind}'")

    # pylint: enable=unused-argument

TEXT = """
server.port=9000
server.error.whitelabel.enabled=false
security.basic.enabled=false
management.security.enabled=false
#spring.cache.ehcache.config=classpath:config/ehcache.xml
# Logging
#logging.level.org.springframework.web=DEBUG
#logging.level.org.hibernate=DEBUG
#logging.level.org.springframework.boot.autoconfigure.security=DEBUG
#logging.level.org.springframework=DEBUG
#logging.level.com.mchange.v2.c3p0.impl=DEBUG
#logging.level.com.mchange=INFO
#logging.level.org.springframework.cache=TRACE
logging.file=/tmp/mslogs/payroll-service.log
spring.datasource.driverClassName=com.mysql.jdbc.Driver
spring.datasource.url=jdbc:mysql://45.55.191.188:3306/cs_payroll?useSSL=false&autoReconnect=true&amp;createDatabaseIfNotExist=true&amp;useUnicode=true&amp;characterEncoding=utf-8
spring.datasource.username=root
spring.datasource.password=gAng34745dev
spring.datasource.testOnBorrow=true
spring.datasource.validationQuery=SELECT 1
spring.datasource.validationQueryTimeout=40
spring.datasource.timeBetweenEvictionRunsMillis=30000
spring.datasource.minEvictableIdleTimeMillis=30000
spring.datasource.removeAbandoned=true
spring.datasource.removeAbandonedTimeout=3000
spring.jpa.database-platform=org.hibernate.dialect.MySQL5Dialect
spring.jpa.show-sql=false
spring.jpa.hibernate.ddl-auto=update
spring.jpa.hibernate.naming-strategy=org.hibernate.cfg.DefaultNamingStrategy
"""

TEXT2 = """
#
# Druid - a distributed column store.
# Copyright 2012 - 2015 Metamarkets Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Extensions (no deep storage model is listed - using local fs for deep storage - not recommended for production)
# Also, for production to use mysql add, "io.druid.extensions:mysql-metadata-storage"
druid.extensions.loadList=["mysql-metadata-storage", "druid-kafka-eight", "druid-s3-extensions"]
druid.extensions.directory=extensions
druid.extensions.hadoopDependenciesDir=hadoopDependenciesDir

# Zookeeper
druid.zk.service.host=company-zookeeper.marathon.mesos:12181

# Metadata Storage (use something like mysql in production by uncommenting properties below)
# by default druid will use derby
druid.metadata.storage.type=mysql
druid.metadata.storage.connector.connectURI=jdbc:mysql://user-db.marathon.mesos:3306/druid
druid.metadata.storage.connector.user=druid
druid.metadata.storage.connector.password=diurd

# Deep storage (local filesystem for examples - don't use this in production)
druid.storage.type=local
druid.storage.storageDirectory=/tmp/druid/localStorage

# setup S3 deep storage
#druid.storage.type=s3
#druid.s3.accessKey=AKIAJRTI7WX3QDFFZCRA
#druid.s3.secretKey=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
#druid.storage.bucket=company-pro-druid-deep-storage
#druid.storage.baseKey=druid-segments

# Query Cache (we use a simple 10mb heap-based local cache on the broker)
druid.cache.type=local
druid.cache.sizeInBytes=10000000

# Coordinator Service Discovery
druid.selectors.coordinator.serviceName=druid-coordinator

# Indexing service discovery
druid.selectors.indexing.serviceName=druid-overlord

# Monitoring (disabled for examples)
# druid.monitoring.monitors=["com.metamx.metrics.SysMonitor","com.metamx.metrics.JvmMonitor"]

# Metrics logging (disabled for examples)
druid.emitter=logging
druid.emitter.logging.logLevel=debug
"""

# def main():
#     """Main."""

#     # Filename to open and analyze
#     source_filename = "application.properties"

#     with open(source_filename, "r", encoding="utf-8") as f:
#         content = f.read()

#     # Analyze file content
#     doc = ApplicationPropertiesAnalyzer()
#     doc.analyze(content=content)

#     # Print key/value pairs from source_filename
#     for n in doc.get_kvps():
#         print(n.key, n.value)

# if __name__ == "__main__":
#     main()
