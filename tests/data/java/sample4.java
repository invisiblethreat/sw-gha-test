package com.vs.ezlicrun;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Serializable;
import java.net.InetAddress;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.StringTokenizer;

public class EzLicenseInfo implements Serializable {
   public static final int EZLIC_KEY_VSN = 20;
   public static final int EZLIC_MODEL_USER = 1;
   public static final int EZLIC_MODEL_SERVER = 2;
   public static final int EZLIC_TYPE_U_USER = 1;
   public static final int EZLIC_TYPE_U_NODE = 2;
   public static final int EZLIC_TYPE_U_FLOAT = 3;
   public static final int EZLIC_TYPE_SVR_CONC = 1;
   public static final int EZLIC_TYPE_SVR_CPU = 2;
   public static final int EZLIC_TYPE_SVR_MHZ = 3;
   public static final int EZLIC_TYPE_SVR_NMU = 4;
   public static final int EZLIC_MODE_TIME = 1;
   public static final int EZLIC_MODE_METERED = 2;
   public static final int EZLIC_MODE_OPTIONS = 4;
   public static final int EZLIC_MODE_CUSTOM_KEY = 8;
   public static final int EZLIC_MODE_CUSTOM_COOKIE = 16;
   private String _$4546 = null;
   private int _$4557 = 0;
   private int _$4574 = 0;
   private int _$4590 = 0;
   private String _$2881 = null;
   private String _$4608 = null;
   private String _$4621 = null;
   private Date _$4637 = null;
   private long _$4652 = 0L;
   private long _$4665 = 0L;
   private String _$4674 = null;
   private boolean _$4682 = false;
   private boolean _$4690 = false;
   private long _$4694 = -1L;
   private long _$4705 = -1L;
   private int _$4720 = 0;
   private String _$4735 = null;
   private int _$4742 = -1;
   private String _$4749 = null;
   private static int _$4762 = -100;
   String spclky = Crypt.decode("dyAuYCM/bV==", "axHtYW==", "ipsic");
   String[] pvtkwds = new String[]{"", "exp", "cpu", "mhz", "cnc", "nmu", "opt", "usr", "hst", "net", "qta", "flt", "cst", "cooky", "cksm", "vsn", "pwd", "expts", "chkid", "who", "when", "ts", "cust", "prod", "enf", ""};
   protected static final int EXP = 1;
   protected static final int CPU = 2;
   protected static final int MHZ = 3;
   protected static final int CNC = 4;
   protected static final int NMU = 5;
   protected static final int OPT = 6;
   protected static final int USR = 7;
   protected static final int HST = 8;
   protected static final int NET = 9;
   protected static final int QTA = 10;
   protected static final int FLT = 11;
   protected static final int CST = 12;
   protected static final int COOKY = 13;
   protected static final int CKSM = 14;
   protected static final int VSN = 15;
   protected static final int PWD = 16;
   protected static final int EXPTS = 17;
   protected static final int CHKID = 18;
   protected static final int WHO = 19;
   protected static final int WHEN = 20;
   protected static final int TS = 21;
   protected static final int CUST = 22;
   protected static final int PROD = 23;
   protected static final int ENF = 24;
   protected static final int NUMPIECES = 24;

   public String getLicenseKey() {
      return this._$4546;
   }

   public int getLicenseModelCode() {
      return this._$4557;
   }

   public int getLicenseTypeCode() {
      return this._$4574;
   }

   public int getLicenseModeBitmap() {
      return this._$4590;
   }

   public String getCustomKey() {
      return this._$2881;
   }

   public String getCustomCookie() {
      return this._$4608;
   }

   public String getUserHostNetName() {
      return this._$4621;
   }

   public Date getExpirationDate() {
      return this._$4652 != (long)0 ? new Date(this._$4652) : this._$4637;
   }

   public long getExpirationTs() {
      return this._$4652;
   }

   public String getOptions() {
      return this._$4674;
   }

   public boolean getEnforce() {
      return this._$4682;
   }

   public long getQuotaValue() {
      return this._$4694;
   }

   public long getUsageValue() {
      return this._$4705;
   }

   public int getWarningsBitmap() {
      return this._$4720;
   }

   public int getKeyVersion() {
      return this._$4742;
   }

   public String getAppPwd() {
      return this._$4690 ? this._$4735 : null;
   }

   public String getChainedKeyId() {
      return this._$4749;
   }

   public void setLicenseKey(String var1) {
      this._$4546 = var1;
   }

   public void setLicenseModelCode(int var1) {
      this._$4557 = var1;
   }

   public void setLicenseTypeCode(int var1) {
      this._$4574 = var1;
   }

   public void setLicenseModeBitmap(int var1) {
      this._$4590 = var1;
   }

   public void setCustomKey(String var1) {
      this._$2881 = var1;
   }

   public void setCustomCookie(String var1) {
      this._$4608 = var1;
   }

   public void setUserHostNetName(String var1) {
      this._$4621 = var1;
   }

   public void setExpirationDate(Date var1) {
      this._$4637 = var1;
      this._$4652 = var1.getTime();
   }

   public void setOptions(String var1) {
      this._$4674 = var1;
   }

   public void setEnforce(boolean var1) {
      this._$4682 = var1;
   }

   public void setQuotaValue(long var1) {
      this._$4694 = var1;
   }

   public void setUsageValue(long var1) {
      this._$4705 = var1;
   }

   public void setWarningsBitmap(int var1) {
      this._$4720 = var1;
   }

   public void setKeyVersion(int var1) {
      this._$4742 = var1;
   }

   protected void setChainedKeyId(String var1) {
      this._$4749 = var1;
   }

   public static String createKeyCookieSeed(String var0) {
      String var1 = null;

      try {
         var1 = (new CookieStruct((new Date()).getTime(), 0L, (String)null)).makeCookie((String)null, var0, (String)null, true, false);
      } catch (Exception var3) {
      }

      return var1;
   }

   public static String createKeyCookieSeed(String var0, String var1, String var2, boolean var3) throws EzLicExceptionBase {
      return (new CookieStruct((new Date()).getTime(), 0L, var2)).makeCookie((String)null, var0, var1, true, var3);
   }

   public static String createKeyCookieSeed(String var0, String var1, String var2, boolean var3, String var4) throws EzLicExceptionBase {
      return (new CookieStruct((new Date()).getTime(), 0L, var2)).makeCookie(var4, var0, var1, true, var3);
   }

   public static boolean cleanupKeyCookie(String var0, String var1, String var2) throws EzLicExceptionBase {
      CookieStruct var3 = CookieStruct.parseCookie(var0, var1, var2);
      return var3.cleanupCookie((String)null, true, var1, var2);
   }

   public static boolean cleanupKeyCookie(String var0, String var1, String var2, String var3, boolean var4) throws EzLicExceptionBase {
      CookieStruct var5 = CookieStruct.parseCookie(var0, var1, var2);
      return var5.cleanupCookie(var3, var4, var1, var2);
   }

   public static String getKeyCookieAppState(String var0, String var1, String var2) throws EzLicExceptionBase {
      CookieStruct var3 = CookieStruct.parseCookie(var0, var1, var2);
      return var3.appState;
   }

   public static long getKeyCookieQuotaToDate(String var0, String var1, String var2) throws EzLicExceptionBase {
      CookieStruct var3 = CookieStruct.parseCookie(var0, var1, var2);
      return var3.quotaToDate;
   }

   public static long getKeyCookieTs(String var0, String var1, String var2) throws EzLicExceptionBase {
      CookieStruct var3 = CookieStruct.parseCookie(var0, var1, var2);
      return var3.ts;
   }

   public int checkSingleUserLicenseKeyBasic(String var1, int var2, long var3, long var5, int var7, long var8, String var10) throws EzLicExceptionBase {
      return this.checkSingleUserLicenseKeyBasic(var1, var2, var3, var5, var7, var8, var10, (String)null, (String)null);
   }

   public int checkSingleUserLicenseKeyBasic(String var1, int var2, long var3, long var5, int var7, long var8, String var10, String var11, String var12) throws EzLicExceptionBase {
      return this.checkLicenseKey(var1, (EzLicCustomLicenseInterface)null, (Object)null, var2, var3, var5, var7, var8, var10, 0L, var11, var12);
   }

   public int checkMultiUserLicenseKeyBasic(String var1, int var2, long var3, long var5, int var7, long var8, String var10, long var11) throws EzLicExceptionBase {
      return this.checkLicenseKey(var1, (EzLicCustomLicenseInterface)null, (Object)null, var2, var3, var5, var7, var8, var10, var11);
   }

   public int checkMultiUserLicenseKeyBasic(String var1, int var2, long var3, long var5, int var7, long var8, String var10, long var11, String var13, String var14) throws EzLicExceptionBase {
      return this.checkLicenseKey(var1, (EzLicCustomLicenseInterface)null, (Object)null, var2, var3, var5, var7, var8, var10, var11, var13, var14);
   }

   public int checkLicenseKey(String var1, EzLicCustomLicenseInterface var2, Object var3, int var4, long var5, long var7, int var9, long var10, String var12, long var13) throws EzLicExceptionBase {
      return this.checkLicenseKey(var1, var2, var3, var4, var5, var7, var9, var10, var12, var13, (String)null, (String)null);
   }

   public int checkLicenseKey(String var1, EzLicCustomLicenseInterface var2, Object var3, int var4, long var5, long var7, int var9, long var10, String var12, long var13, String var15, String var16) throws EzLicExceptionBase {
      return this.checkLicenseKey(var1, var2, var3, var4, var5, var7, var9, var10, var12, var13, var15, var16, (String)null, true);
   }

   public int checkLicenseKey(String var1, EzLicCustomLicenseInterface var2, Object var3, int var4, long var5, long var7, int var9, long var10, String var12, long var13, String var15, String var16, String var17, boolean var18) throws EzLicExceptionBase {
      if (var1 == null || var15 == null && var16 != null) {
         EzLicExceptionBase.throwLicenseException(13, "Bad params to checkLicenseKey: licenseKey and / or product / application passwd combo");
      }

      this._$5926();
      long var19 = (new Date()).getTime();
      long var21 = 0L;
      if (var18) {
         var21 = Hfile.getHfileTs(var17, true, var19);
         Hfile.updateHfile(var17, var19);
      }

      boolean var23 = false;
      boolean var24 = false;
      String var25 = null;
      long var26 = -1L;
      int var28 = -1;
      String var29 = Crypt.decode("dyAuYCM/bV==", var1, "thekey");
      if (checkDebug(0)) {
         System.out.println("In EzLicenseInfo.checkLicenseKey.  Decoded license string:");
         System.out.println(var29);
      }

      StringTokenizer var30 = new StringTokenizer(var29, ":");
      this._$4546 = var1;
      String var31 = Crypt.decode("dyAuYCM/bV==", "QtejQ8G/WciuXr==", this.spclky);
      this._$4690 = var12 != null && var12.equals(var31);

      String var32;
      String var33;
      String var34;
      while(var30.hasMoreTokens()) {
         var32 = null;
         var33 = null;
         var34 = var30.nextToken();
         if (checkDebug(5)) {
            System.out.println(String.valueOf("tok: ").concat(String.valueOf(var34)));
         }

         StringTokenizer var35 = new StringTokenizer(var34, "=");
         if (var35.hasMoreTokens() && (var32 = var35.nextToken()) == null || var35.hasMoreTokens() && var35.nextToken() == null) {
            EzLicExceptionBase.throwLicenseException(1, (String)null);
         }

         int var36 = this.lookupKey(var32);
         if (var36 == 0) {
            EzLicExceptionBase.throwLicenseException(1, (String)null);
         }

         var33 = var34.substring(var34.indexOf("=") + 1).replace('|', ':');
         if (checkDebug(8)) {
            System.out.println(String.valueOf(String.valueOf(String.valueOf("In EzLicenseInfo.checkLicenseKey.  kwd=").concat(String.valueOf(var32))).concat(String.valueOf(",val="))).concat(String.valueOf(var33)));
         }

         switch(var36) {
         case 1:
         case 17:
            if (var21 == (long)0) {
               var21 = Hfile.getHfileTs(var17, true, var19);
               Hfile.updateHfile(var17, var19);
            }

            this._$6084(var19, var36, var33);
            this._$4590 |= 1;
            break;
         case 2:
         case 3:
         case 4:
         case 5:
            if (this._$4557 == 1) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4705 = this.checkLongValue("Server limit", var33, this._$4705, var13, 0L);
            switch(var36) {
            case 2:
               this._$4574 = 2;
               break;
            case 3:
               this._$4574 = 3;
               break;
            case 4:
               this._$4574 = 1;
               break;
            default:
               this._$4574 = 4;
            }

            this._$4557 = 2;
            break;
         case 6:
            if (this._$4674 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4674 = var33;
            this._$4590 |= 4;
            break;
         case 7:
            if (this._$4557 == 2 || this._$4621 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4557 = 1;
            this._$4574 = 1;
            if (var12 != null && !this._$4690 && !compareOsd(var33, var12)) {
               EzLicExceptionBase.throwLicenseException(4, (String)null);
            }

            this._$4621 = var33;
            break;
         case 8:
         case 9:
            if (this._$4621 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            if (var12 != null && !var12.equals(var31) && !var12.equals(Crypt.encode("dyAuYCM/bV==", "zapowakah", "foohfah")) && !compareOsd(var33, var12)) {
               EzLicExceptionBase.throwLicenseException(4, (String)null);
            }

            this._$4621 = var33;
            break;
         case 10:
            this._$4694 = this.checkLongValue("Metered quota", var33, this._$4694, var5, var10);
            if (var5 >= (long)0) {
               if (!this._$4690 && var10 > this._$4694 / (long)4 && var10 > (long)5) {
                  var10 = this._$4694 / (long)4;
                  if (var5 > this._$4694 + var10) {
                     EzLicExceptionBase.throwLicenseException(3, String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf("Quota Limit: ").concat(String.valueOf(this._$4694))).concat(String.valueOf(", Current: "))).concat(String.valueOf(var5))).concat(String.valueOf(", Grace: "))).concat(String.valueOf(var10)));
                  }

                  this._$4720 |= 16;
               }

               if (this._$4694 < var5) {
                  this._$4720 |= 8;
               } else if (this._$4694 - var5 <= var7) {
                  this._$4720 |= 2;
               }
            }

            this._$4590 |= 2;
            break;
         case 11:
            this._$4705 = this.checkLongValue("Floating user limit", var33, this._$4705, var13, 0L);
            this._$4557 = 1;
            this._$4574 = 3;
            break;
         case 12:
            if (this._$2881 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$2881 = var33;
            this._$4590 |= 8;
            break;
         case 13:
            if (this._$4608 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4608 = var33;
            this._$4590 |= 16;
            break;
         case 14:
            if (var23) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            try {
               var28 = Integer.parseInt(var33);
               var23 = true;
            } catch (Exception var39) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }
            break;
         case 15:
            if (this._$4742 > 0) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            try {
               this._$4742 = Integer.parseInt(var33);
            } catch (Exception var38) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }
            break;
         case 18:
            if (this._$4749 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4749 = var33;
         case 16:
            if (this._$4735 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4735 = var33;
         case 19:
         case 20:
         case 22:
         default:
            break;
         case 21:
            try {
               this._$4665 = Long.parseLong(var33);
            } catch (Exception var40) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            if (this._$4665 - var19 > 21600000L) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }
            break;
         case 23:
            if (var25 != null) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            var25 = var33;
            break;
         case 24:
            if (this._$4682) {
               EzLicExceptionBase.throwLicenseException(1, (String)null);
            }

            this._$4682 = true;
         }
      }

      if (var23 && var28 != makeChecksum(var29.substring(0, var29.lastIndexOf(":")))) {
         if (checkDebug(1)) {
            System.out.println(String.valueOf("** Checksum mismatch.  Checksum: ").concat(String.valueOf(var28)));
         }

         EzLicExceptionBase.throwLicenseException(1, (String)null);
      }

      if (this._$4557 == 0 && this._$4621 != null) {
         this._$4557 = 1;
         this._$4574 = 2;
      }

      if ((this._$4590 & 1) != 0) {
         this._$6175(var19, (long)var4, (long)var9);
      }

      if (this._$4621 == null) {
         EzLicExceptionBase.throwLicenseException(1, (String)null);
      }

      if (var12 == null) {
         if (!this._$4682) {
            EzLicExceptionBase.throwLicenseException(4, (String)null);
         }
      } else if (!this._$4690 && !compareOsd(this._$4621, var12)) {
         EzLicExceptionBase.throwLicenseException(4, (String)null);
      }

      if (this._$4682 && (var12 == null || !this._$4690)) {
         var32 = null;
         var33 = null;
         var34 = System.getProperty("user.name");
         if (checkDebug(2)) {
            System.out.println(String.valueOf("OS user name: ").concat(String.valueOf(var34)));
         }

         int var42 = this._$4621.indexOf("@");
         if (var42 > 0 && var42 < this._$4621.length()) {
            var32 = this._$4621.substring(var42 + 1);
            var33 = this._$4621.substring(0, var42);
         } else if (this._$4557 == 1 && this._$4574 == 1) {
            var33 = this._$4621;
         } else {
            var32 = this._$4621;
         }

         if (var33 != null && !compareOsd(var34, var33)) {
            EzLicExceptionBase.throwLicenseException(4, (String)null);
         }

         if (var32 != null) {
            String var43 = null;

            try {
               var43 = InetAddress.getLocalHost().getHostName().trim();
               if (checkDebug(2)) {
                  System.out.println(String.valueOf(String.valueOf("Host name according to name server: [").concat(String.valueOf(var43))).concat(String.valueOf("]")));
               }
            } catch (Throwable var41) {
               if (checkDebug(2)) {
                  System.out.println(String.valueOf("*** Exception during getLocalHost/getHostName.  Message:\n").concat(String.valueOf(var41.getMessage())));
               }

               var43 = "";
            }

            if (!compareOsd(var43, var32)) {
               EzLicExceptionBase.throwLicenseException(4, (String)null);
            }
         }
      }

      if (this._$4735 != null) {
         var32 = PkCrypt.makePublicKey(this._$4735);
         if (!this._$4690 && (var16 == null || !var32.equals(var16) || !var15.equals(var25))) {
            if (checkDebug(5)) {
               System.out.println("Problem w/ password-protected key. Reason:");
               if (var16 == null) {
                  System.out.println("API call doesn't specify a password");
               } else if (!var32.equals(var16)) {
                  System.out.println(String.valueOf(String.valueOf(String.valueOf(String.valueOf("AppPwdPubkey '").concat(String.valueOf(var32))).concat(String.valueOf("' doesn't match API password '"))).concat(String.valueOf(var16))).concat(String.valueOf("'")));
               } else {
                  System.out.println(String.valueOf(String.valueOf(String.valueOf(String.valueOf("Product '").concat(String.valueOf(var15))).concat(String.valueOf("' doesn't match product name '"))).concat(String.valueOf(var25))).concat(String.valueOf("'")));
               }
            }

            EzLicExceptionBase.throwLicenseException(14, (String)null);
         }

         if (checkDebug(5)) {
            System.out.println(String.valueOf(String.valueOf(String.valueOf(String.valueOf("appPwd: '").concat(String.valueOf(this._$4735))).concat(String.valueOf("', public key: '"))).concat(String.valueOf(var32))).concat(String.valueOf("'")));
         }

         if (this._$2881 != null) {
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("Decrypted custom key:\n'").concat(String.valueOf(this.getCustomKey()))).concat(String.valueOf("'\nto:")));
            }

            this._$2881 = PkCrypt.decryptWithPublicKey(this._$2881, var32);
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("'").concat(String.valueOf(this.getCustomKey()))).concat(String.valueOf("'")));
            }
         }

         if (this._$4608 != null) {
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("Decrypted custom cookie:\n'").concat(String.valueOf(this.getCustomCookie()))).concat(String.valueOf("'\nto:")));
            }

            this._$4608 = PkCrypt.decryptWithPublicKey(this._$4608, var32);
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("'").concat(String.valueOf(this.getCustomCookie()))).concat(String.valueOf("'")));
            }
         }

         if (this._$4674 != null && this._$4674.startsWith("98765")) {
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("Decrypted options:\n'").concat(String.valueOf(this.getOptions()))).concat(String.valueOf("'\nto:")));
            }

            this._$4674 = PkCrypt.decryptWithPublicKey(this._$4674.substring(5), var32);
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf("'").concat(String.valueOf(this._$4674))).concat(String.valueOf("'")));
            }
         }
      }

      if (var2 != null) {
         this._$4720 |= var2.checkCustomKeyCode(this._$2881, var3);
      }

      if (checkDebug(1)) {
         System.out.println(String.valueOf("License key check ok.  Warning bit map: ").concat(String.valueOf(this._$4720)));
      }

      return this._$4720;
   }

   public String checkLicenseKeySecure(String var1, String var2, EzLicExceptionBase var3, EzLicCustomLicenseInterface var4, Object var5, int var6, long var7, long var9, int var11, long var12, String var14, long var15) throws EzLicExceptionBase {
      return this.checkLicenseKeySecure(var1, var2, var3, var4, var5, var6, var7, var9, var11, var12, var14, var15, (String)null, (String)null, (String)null);
   }

   public String checkLicenseKeySecure(String var1, String var2, EzLicExceptionBase var3, EzLicCustomLicenseInterface var4, Object var5, int var6, long var7, long var9, int var11, long var12, String var14, long var15, String var17, String var18, String var19) throws EzLicExceptionBase {
      return this.checkLicenseKeySecure(var1, var2, var3, var4, var5, var6, var7, var9, var11, var12, var14, var15, var17, var18, var19, (String)null, true);
   }

   public String checkLicenseKeySecure(String var1, String var2, EzLicExceptionBase var3, EzLicCustomLicenseInterface var4, Object var5, int var6, long var7, long var9, int var11, long var12, String var14, long var15, String var17, String var18, String var19, String var20, boolean var21) throws EzLicExceptionBase {
      long var22 = (new Date()).getTime();
      CookieStruct var24 = var2 == null ? null : CookieStruct.parseCookie(var2, var17, var18, var21, var22);
      int var25 = this.checkLicenseKey(var1, var4, var5, var6, var7, var9, var11, var12, var14, var15, var17, var18, var20, var21);
      String var26 = null;
      if (var24 != null) {
         if (!var21 && (this._$4590 & 1) != 0 && Hfile.olderThan(var22, var24.ts)) {
            EzLicExceptionBase.throwLicenseException(11, "Tampered system clock");
         }

         if ((this._$4590 & 2) != 0 && var7 < (long)0) {
            if (!this._$4690 && var12 > this._$4694 / (long)4 && var12 > (long)5) {
               var12 = this._$4694 / (long)4;
               var25 |= 16;
               if (checkDebug(7)) {
                  System.out.println(String.valueOf(String.valueOf(String.valueOf("Truncating grace down to ").concat(String.valueOf(var12))).concat(String.valueOf(".  Key quota value is "))).concat(String.valueOf(this._$4694)));
               }
            }

            if (checkDebug(10)) {
               System.out.println(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf("Metered license secure API state update: key quotaValue=").concat(String.valueOf(this._$4694))).concat(String.valueOf(", cooky quotaToDate="))).concat(String.valueOf(var24.quotaToDate))).concat(String.valueOf(", quota incr = "))).concat(String.valueOf(var7)));
            }

            long var27 = this._$4694 - var24.quotaToDate + var7;
            if (var27 >= (long)0 && var27 <= var9) {
               var25 |= 2;
            } else if (var27 < (long)0 && -var27 <= var12) {
               var25 |= 8;
            } else if (var27 < (long)0) {
               EzLicExceptionBase.throwLicenseException(3, String.valueOf(String.valueOf(String.valueOf("Quota limit: ").concat(String.valueOf(String.valueOf(this._$4694)))).concat(String.valueOf(", Current increment: "))).concat(String.valueOf(String.valueOf(var7))));
            }
         }

         if (var7 < (long)0) {
            var24.quotaToDate += -var7;
         }

         var24.ts = var22;
         var24.appState = var19;
         var26 = var24.makeCookie(var20, var17, var18, true, false);
      }

      if (var3 == null) {
         return var26;
      } else {
         var3.setMessage(var26);
         var3.setMessageCode(var25);
         throw var3;
      }
   }

   private void _$6084(long var1, int var3, String var4) throws EzLicExceptionBase {
      if (this._$4637 != null) {
         EzLicExceptionBase.throwLicenseException(1, (String)null);
      }

      if (var3 == 1) {
         this._$4637 = this.makeDate(var4, 1);
         if (this._$4637 == null) {
            EzLicExceptionBase.throwLicenseException(1, (String)null);
         }

         this._$4652 = this._$4637.getTime();
      } else {
         try {
            this._$4652 = Long.parseLong(var4);
         } catch (Throwable var6) {
            EzLicExceptionBase.throwLicenseException(1, (String)null);
         }

         this._$4637 = new Date(this._$4652);
      }

   }

   private void _$6175(long var1, long var3, long var5) throws EzLicExceptionBase {
      long var7 = this._$4652 - var1;
      long var9 = this._$4652 - this._$4665;
      long var11 = var9 / (long)86400000;
      long var13 = var5 * 86400000L;
      if (var1 > this._$4652) {
         long var15 = var9 / (long)4;
         if (checkDebug(5)) {
            System.out.println(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf("expired.  timediff ").concat(String.valueOf(var7))).concat(String.valueOf(", maxgraceMs "))).concat(String.valueOf(var15))).concat(String.valueOf(", graceMs "))).concat(String.valueOf(var13))).concat(String.valueOf(", daysGrace "))).concat(String.valueOf(var5)));
         }

         if (!this._$4690 && var15 < var13 && var5 > (long)5) {
            var13 = var15;
            var5 = var15 / (long)86400000;
            if (checkDebug(5)) {
               System.out.println(String.valueOf(String.valueOf(String.valueOf("truncating expiration.  new timegrace ").concat(String.valueOf(var15))).concat(String.valueOf(", new days grace "))).concat(String.valueOf(var5)));
            }

            this._$4720 |= 32;
         }

         if (-var7 <= var13) {
            this._$4720 |= 4;
         } else {
            EzLicExceptionBase.throwLicenseException(2, String.valueOf("Expired on ").concat(String.valueOf((new SimpleDateFormat("yyyy-MMMM-dd 'at' HH:mm:ss z")).format(this._$4637))));
         }
      } else if (var7 < var3 * (long)86400000) {
         this._$4720 |= 1;
      }

   }

   protected Date makeDate(String var1, int var2) {
      Date var3 = null;
      var1 = var1.trim();

      try {
         SimpleDateFormat var4 = new SimpleDateFormat("yyyy-MM-dd");
         var3 = var4.parse(var1);
         if (var2 > 0) {
            var3 = new Date(var3.getTime() + (long)(var2 * 24 * 3600 * 1000));
         }

         if (var1.length() != 10 || var1.indexOf("-") != 4 || var1.lastIndexOf("-") != 7) {
            Object var5 = null;
            return (Date)var5;
         }
      } catch (Exception var6) {
         var3 = null;
      }

      return var3;
   }

   protected long checkLongValue(String var1, String var2, long var3, long var5, long var7) throws EzLicExceptionBase {
      if (var3 != (long)-1) {
         EzLicExceptionBase.throwLicenseException(1, (String)null);
      }

      try {
         var3 = Long.parseLong(var2);
      } catch (Exception var10) {
         EzLicExceptionBase.throwLicenseException(1, (String)null);
      }

      if (var3 < var5 && var5 - var3 > var7) {
         EzLicExceptionBase.throwLicenseException(3, String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf(String.valueOf("Details: ").concat(String.valueOf(var1))).concat(String.valueOf(": "))).concat(String.valueOf(String.valueOf(var3)))).concat(String.valueOf(", Current: "))).concat(String.valueOf(String.valueOf(var5)))).concat(String.valueOf(", Grace: "))).concat(String.valueOf(var7)));
      }

      return var3;
   }

   protected int lookupKey(String var1) {
      boolean var2 = false;

      for(int var3 = 1; var3 <= 24; ++var3) {
         if (this.pvtkwds[var3].equals(var1)) {
            return var3;
         }
      }

      return 0;
   }

   protected static int makeChecksum(String var0) {
      int var1 = 0;

      for(int var2 = 0; var2 < var0.length(); ++var2) {
         var1 += var0.charAt(var2);
      }

      return var1;
   }

   protected static boolean checkDebug(int var0) {
      if (_$4762 == -100) {
         String var1 = Crypt.decode("dyAuYCM/bV==", "HD/aFCHUDCLe", "hoowah");
         String var2 = "";

         try {
            InputStream var3 = Runtime.getRuntime().exec("env").getInputStream();
            BufferedReader var4 = new BufferedReader(new InputStreamReader(var3));

            while((var2 = var4.readLine()) != null && !var2.startsWith(var1)) {
            }

            if (var2 != null && !var2.equals("")) {
               _$4762 = Integer.parseInt(var2.substring(var2.indexOf("=") + 1).trim());
            } else {
               _$4762 = -1;
            }
         } catch (Exception var5) {
            _$4762 = -1;
         }
      }

      return _$4762 >= var0;
   }

   protected static boolean compareOsd(String var0, String var1) {
      if (var0 != null && var1 != null) {
         boolean var2 = System.getProperty("os.name").startsWith("Windows");
         return var2 ? var0.equalsIgnoreCase(var1) : var0.equals(var1);
      } else {
         return false;
      }
   }

   private void _$5926() {
      this._$4546 = null;
      this._$4557 = 0;
      this._$4574 = 0;
      this._$4590 = 0;
      this._$2881 = null;
      this._$4608 = null;
      this._$4621 = null;
      this._$4637 = null;
      this._$4652 = 0L;
      this._$4674 = null;
      this._$4682 = false;
      this._$4694 = -1L;
      this._$4705 = -1L;
      this._$4720 = 0;
      this._$4735 = null;
      this._$4742 = -1;
   }
}
