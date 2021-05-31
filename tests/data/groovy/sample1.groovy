import com.amazonaws.auth.BasicAWSCredentials
import com.amazonaws.internal.StaticCredentialsProvider
import com.amazonaws.services.s3.AmazonS3Client
import com.amazonaws.services.s3.model.GetObjectRequest
import com.datastax.driver.core.Cluster
import java.security.MessageDigest
import static com.datastax.driver.core.querybuilder.QueryBuilder.bindMarker
import static com.datastax.driver.core.querybuilder.QueryBuilder.insertInto
import static com.xlson.groovycsv.CsvParser.parseCsv
@Grab('com.xlson.groovycsv:groovycsv:1.1')
@Grab('com.datastax.cassandra:cassandra-driver-core:3.0.0-rc1')
@Grab(group='com.amazonaws', module='aws-java-sdk', version='1.10.27')
@groovy.lang.GrabExclude("commons-logging:commons-logging")
def clientId = 'AKIAIDMUIY2QZLABJ65Q'
def clientSecret = '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'
final String cassandra_address = args[0];
def bucketName = 'quickstream-data'
def cluster = Cluster.builder().addContactPoint(cassandra_address).build();
def session = cluster.connect()
def fileName = args[1]
def s3client = new AmazonS3Client(new StaticCredentialsProvider(new BasicAWSCredentials(clientId, clientSecret)))
def assetObjectRequest = new GetObjectRequest(bucketName, fileName);
def revisionObject = s3client.getObject(assetObjectRequest);
def revisionsData = parseCsv(new InputStreamReader(revisionObject.getObjectContent()))
def insertRevision = session.prepare(insertInto("acs", "revisions")
        .value("asset_id", bindMarker("asset_id"))
        .value("id", bindMarker("id"))
        .value("created", bindMarker("created"))
        .value("content_type", bindMarker("content_type"))
        .value("datalocation", bindMarker("datalocation"))
        .value("empty", bindMarker("empty")))
//.value("tags"))
for(line in revisionsData) {
    def boundStatement = insertRevision.bind()
            .setString("id", line.ID)
            .setString("asset_id", line.OBJ_ID)
            .setTimestamp("created", Date.parse("MMM dd yyyy H:m", line.OBJ_DATETIME))
            .setBool("empty", Boolean.parseBoolean(line.EMPTY))
            .setString("datalocation", MessageDigest.getInstance("MD5").digest(line.PATH.bytes).encodeHex().toString())
    session.executeAsync(boundStatement)
    println("inserted revision $line.ID")
session.close();
println("completed ");
System.exti(0);