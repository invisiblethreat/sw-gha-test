
# Variable assignment

Token.Name 
Token.Operator
Token.String

private static final String APPLICATION_PASSWORD = "arFNTeFdbetraMtEbvtwU4==";

# Various notes/examples for pygments

## Java Function call

Token.Name.Attribute 'println'
Token.Operator '('
Token.Literal.String '"LicenseInspector: Error in parsing license information."'

System.err.println("LicenseInspector: Error in parsing license information.");

## Java Boolean

Token.Name.Attribute 'getNodeName'
Token.Operator '('
Token.Operator ')'
Token.Text ' '
Token.Operator '='
Token.Operator '='
Token.Text ' '
Token.Literal.String '"key"'

if (var3.item(var5).getNodeName() == "key") {

## Java Function arguments

Token.Literal.String '"SpectraGuard Enterprise"'
Token.Operator ','
Token.Text ' '
Token.Literal.String '"arFNTeFdbetraMtEbvtwU4=="'
var4.checkLicenseKey(var3, (EzLicCustomLicenseInterface)null, (Object)null, 7, 0L, 10L, 0, 0L, "user", 0L, "SpectraGuard Enterprise", "arFNTeFdbetraMtEbvtwU4==", (String)null, false);

