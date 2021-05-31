"""Example ApplicationProperties"""

from ContentAnalyzer.analyzers.applicationproperties import ApplicationPropertiesAnalyzer
doc = ApplicationPropertiesAnalyzer()
content = """AppName = "tokenmama-adx"

BaseUrl = "https://tokenmama.io"

CDNUrl = "https://tmm-adx.tianxi100.com/"

CreativeCDN = "https://tmm-ad.tianxi100.com"

AdUrl = "https://adx.tokenmama.io/t/"

AdImpUrl = "https://adx.tokenmama.io/i/"

PublisherDomain = "https://media.tokenmama.io"

AdvertiserDomain = "https://adx.tokenmama.io"

CookieDomain = "tokenmama.io"

Port = 8005

UI = "./ui/dist"

Template = "/opt/adx-templates"

LogPath = "/tmp/tokenmama-adx"

ClickhouseDSN = "tcp://120.55.144.72:10100?username=tm&password=gthSSKD0345"

Geth = "https://mainnet.infura.io/NlT37dDxuLT2tlZNw3It"

SlackToken = "xoxp-340014960567-338241194720-339563622341-94fcb61ce9353b2b0f5a86d4e99580d8"

SlackAdminChannelID = "G9Y7METUG"

TwilioToken = "khWDR6abzUyqzM1WHy9Tfq7P2jRoEhLA"

TelegramBotToken = "547738949:AAFJLOcFctmNEK5wDRDpWP8lE107T7p8XQU"

TelegramBotName = "TokenmeBot"

GeoIP = "/etc/GeoLite2-Country.mmdb"

TokenSalt = "20eefe8d82ba3ca8a417e14a48d24632bc35bbd7"

LinkSalt = "675f6ca23bf616fdb9b06a8d661b4b939f138038"

SentryDSN = "https://6a576b1028974e93a5e2d29071c0e896:fc012faed5a94a3683f435714e1dc2e1@sentry.io/1163662"

AuctionRate = 110.0

AdJSVer = "93c5ef570a12016a58e8"

[Airdrop]
CommissionFee = 4
GasPrice = 4
GasLimit = 210000
DealerContractGasPrice = 5
DealerContractGasLimit = 210000

[MySQL]
Host = "tokenme.c4evkvyvqy7m.ap-northeast-1.rds.amazonaws.com:3306"
User = "tokenme"
Passwd = "tokenmeCRICSUKI2"
DB = "adx"

[Redis]
Master = "tokenme-001.0gguww.0001.apne1.cache.amazonaws.com:6379"
Slave = "tokenme-002.0gguww.0001.apne1.cache.amazonaws.com:6379"

[SQS]
AccountId = "744515144782"
AK = "AKIAIE6OOGPGR3YUIM2Q"
Secret = "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"
Region = "ap-northeast-1"
EmailQueue = "email"
AdClickQueue = "adclick"
AdImpQueue = "adimp"

[S3]
AK = "AKIAJTH2WS5SAVV6OR2A"
Secret = "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"
AdBucket = "tmm-ads"
CreativePath = "creatives"

[Mail]
Server = "smtp.sendgrid.net"
Port = 587
User = "apikey"
Passwd = "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"

[Mail]
Server = "smtp.sendgrid.net"
Port = 587
User = "apikey"
Passwd = "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"

[Zz253]
Account = "N5692616"
Password = "4mNud0qth"
"""

doc.analyze(content)
kvps = doc.get_kvps()
for kvp in kvps:
    print(kvp)
