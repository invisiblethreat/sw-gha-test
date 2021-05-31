"""Java Base"""

from typing import List

import attr
import javalang

from ContentAnalyzer.base import KeyValuePair


@attr.s(kw_only=True, slots=True)
class JavaAnalyzer:
    """JavaAnalyzer."""

    kvps: List[KeyValuePair] = attr.ib(factory=list)

    def analyze(self, content: str) -> None:
        """Analyze content.

        Args:

            content (str): Content to analyze.
        """

        from ContentAnalyzer.analyzers.java.parser import JavaVisitor

        visitor = JavaVisitor(text=content)

        tree = javalang.parse.parse(content)
        visitor.visit(tree)
        self.kvps = visitor.get_matches()


    def get_kvps(self) -> List[KeyValuePair]:
        """Get a list of KeyValuePairs.

        Returns:

            list: List of KeyValuePairs.
        """
        return self.kvps.copy()


# pylint: disable=line-too-long
TEXT = """import com.vs.ezlicrun.EzLicCustomLicenseInterface;
import com.vs.ezlicrun.EzLicExceptionBase;
import com.vs.ezlicrun.EzLicenseInfo;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.NoSuchElementException;
import java.util.StringTokenizer;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class LicenseInspector {
   public static final String LICENSE_FILE_NAME = "licenseKey.xml";
   private static final String USER_HOST = "user";
   public static final String PRODUCT_NAME = "SpectraGuard Enterprise";
   private static final String APPLICATION_PASSWORD = "arFNTeFdbetraMtEbvtwU4==";
   private static final String PROGNAME = "LicenseInspector";
   private static final String KEY_NODE_STRING = "key";
   private static final String EXPIRY_DATE = "EXPIRATION_DATE";

   private static HashMap getKeyMap(EzLicenseInfo var0) {
      if (var0 != null && var0.getOptions() != null) {
         StringTokenizer var1 = new StringTokenizer(var0.getOptions(), ";");
         HashMap var2 = new HashMap();

         try {
            while(var1.hasMoreTokens()) {
               StringTokenizer var3 = new StringTokenizer(var1.nextToken(), "=");
               String var4 = var3.nextToken();
               String var5 = var3.nextToken();
               var2.put(var4, var5);
            }
         } catch (NoSuchElementException var6) {
            System.err.println("LicenseInspector: Error in parsing license information.");
            System.exit(127);
         }

         return var2;
      } else {
         return null;
      }
   }

   public static Document readXML(String var0) {
      Document var1 = null;

      try {
         var1 = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(var0);
         return var1;
      } catch (Exception var3) {
         return null;
      }
   }

   private static String getEncryptedKeyFromXMLLicense(String var0) {
      Document var1 = readXML(var0);
      if (var1 == null) {
         return null;
      } else {
         Element var2 = var1.getDocumentElement();
         NodeList var3 = var2.getChildNodes();
         Node var4 = null;

         for(int var5 = 0; var5 < var3.getLength(); ++var5) {
            if (var3.item(var5).getNodeName() == "key") {
               var4 = var3.item(var5);
            }
         }

         if (var4 != null) {
            NodeList var6 = var4.getChildNodes();
            if (var6 != null) {
               return var6.item(0).getNodeValue();
            }
         }

         return null;
      }
   }

   public static void main(String[] var0) {
      if (var0.length < 1) {
         System.err.println("Usage: java LicenseInspector <keyfile-path> [<param> ...]");
         System.exit(127);
      }

      String var1 = var0[0];
      boolean var2 = var0.length == 1;
      String var3 = getEncryptedKeyFromXMLLicense(var1);
      if (var3 == null) {
         System.err.println("LicenseInspector: Corrupted or missing license.");
         System.exit(127);
      }

      EzLicenseInfo var4 = new EzLicenseInfo();

      try {
         var4.checkLicenseKey(var3, (EzLicCustomLicenseInterface)null, (Object)null, 7, 0L, 10L, 0, 0L, "user", 0L, "SpectraGuard Enterprise", "arFNTeFdbetraMtEbvtwU4==", (String)null, false);
      } catch (EzLicExceptionBase var14) {
         System.err.println("LicenseInspector: Invalid or expired license");
         System.err.println(var14.getMessage());
         System.exit(1);
      }

      HashMap var5 = getKeyMap(var4);
      if (var5 == null) {
         System.err.println("LicenseInspector:null license map");
         System.exit(1);
      }

      SimpleDateFormat var6 = new SimpleDateFormat("dd-MM-yy");
      String var7 = (String)var5.get("EXPIRATION_DATE");
      if (var7 == null) {
         System.err.println("LicenseInspector: No expiry date in license!");
         System.exit(127);
      }

      Date var8 = null;

      Date var9;
      try {
         var9 = var6.parse(var7);
         Date var10 = var4.getExpirationDate();
         var8 = var9;
         if (var10 != null && var10.compareTo(var9) < 0) {
            var8 = var10;
         }
      } catch (Exception var13) {
         System.err.println(var13);
         System.err.println("LicenseInspector: Invalid date in license.");
         System.exit(127);
      }

      var9 = new Date(System.currentTimeMillis());
      if (var8.compareTo(var9) < 0) {
         System.err.println("LicenseInspector: License expired.");
         System.exit(1);
      }

      String var11;
      if (var2) {
         Iterator var15 = var5.keySet().iterator();

         while(var15.hasNext()) {
            var11 = (String)((String)var15.next());
            String var12 = (String)((String)var5.get(var11));
            System.out.println(var11 + "=" + var12);
         }
      } else {
         for(int var16 = 1; var16 < var0.length; ++var16) {
            var11 = (String)var5.get(var0[var16]);
            if (var11 != null) {
               System.out.println(var0[var16] + "=" + var11);
            }
         }
      }

      System.exit(0);
   }
}
"""
# pylint: enable=line-too-long


# def main():
#     """Main."""

#     filename = "tests/data/java/sample4.java"
#     content = open(filename, 'r', encoding='utf-8').read()
#     # content = TEXT

#     doc = JavaAnalyzer()
#     doc.analyze(content)

#     for kvp in doc.get_kvps():
#         print(kvp.to_dict())

#     print("", end='')


# if __name__ == "__main__":
#     main()
