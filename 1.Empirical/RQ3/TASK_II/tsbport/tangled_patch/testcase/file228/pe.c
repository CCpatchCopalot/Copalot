/***************************************************************************
 *                                  _   _ ____  _
 *  Project                     ___| | | |  _ \| |
 *                             / __| | | | |_) | |
 *                            | (__| |_| |  _ <| |___
 *                             \___|\___/|_| \_\_____|
 *
 * Copyright (C) Daniel Stenberg, <daniel@haxx.se>, et al.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution. The terms
 * are also available at https://curl.se/docs/copyright.html.
 *
 * You may opt to use, copy, modify, merge, publish, distribute and/or sell
 * copies of the Software, and permit persons to whom the Software is
 * furnished to do so, under the terms of the COPYING file.
 *
 * This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
 * KIND, either express or implied.
 *
 * SPDX-License-Identifier: curl
 *
 ***************************************************************************/

#include "curl_setup.h"

#if defined(USE_GNUTLS) || defined(USE_WOLFSSL) ||      \
  defined(USE_SCHANNEL) || defined(USE_SECTRANSP)

#if defined(USE_WOLFSSL) || defined(USE_SCHANNEL)
#define WANT_PARSEX509 /* uses Curl_parseX509() */
#endif

#if defined(USE_GNUTLS) || defined(USE_SCHANNEL) || defined(USE_SECTRANSP)
#define WANT_EXTRACT_CERTINFO /* uses Curl_extract_certinfo() */
#define WANT_PARSEX509 /* ... uses Curl_parseX509() */
#endif

#include <curl/curl.h>
#include "urldata.h"
#include "strcase.h"
#include "curl_ctype.h"
#include "hostcheck.h"
#include "vtls/vtls.h"
#include "vtls/vtls_int.h"
#include "sendf.h"
#include "inet_pton.h"
#include "curl_base64.h"
#include "x509asn1.h"
#include "dynbuf.h"

/* The last 3 #include files should be in this order */
#include "curl_printf.h"
#include "curl_memory.h"
#include "memdebug.h"

/*
 * Constants.
 */

/* Largest supported ASN.1 structure. */
#define CURL_ASN1_MAX                   ((size_t) 0x40000)      /* 256K */

/* ASN.1 classes. */
#define CURL_ASN1_UNIVERSAL             0
#define CURL_ASN1_APPLICATION           1
#define CURL_ASN1_CONTEXT_SPECIFIC      2
#define CURL_ASN1_PRIVATE               3

/* ASN.1 types. */
#define CURL_ASN1_BOOLEAN               1
#define CURL_ASN1_INTEGER               2
#define CURL_ASN1_BIT_STRING            3
#define CURL_ASN1_OCTET_STRING          4
#define CURL_ASN1_NULL                  5
#define CURL_ASN1_OBJECT_IDENTIFIER     6
#define CURL_ASN1_OBJECT_DESCRIPTOR     7
#define CURL_ASN1_INSTANCE_OF           8
#define CURL_ASN1_REAL                  9
#define CURL_ASN1_ENUMERATED            10
#define CURL_ASN1_EMBEDDED              11
#define CURL_ASN1_UTF8_STRING           12
#define CURL_ASN1_RELATIVE_OID          13
#define CURL_ASN1_SEQUENCE              16
#define CURL_ASN1_SET                   17
#define CURL_ASN1_NUMERIC_STRING        18
#define CURL_ASN1_PRINTABLE_STRING      19
#define CURL_ASN1_TELETEX_STRING        20
#define CURL_ASN1_VIDEOTEX_STRING       21
#define CURL_ASN1_IA5_STRING            22
#define CURL_ASN1_UTC_TIME              23
#define CURL_ASN1_GENERALIZED_TIME      24
#define CURL_ASN1_GRAPHIC_STRING        25
#define CURL_ASN1_VISIBLE_STRING        26
#define CURL_ASN1_GENERAL_STRING        27
#define CURL_ASN1_UNIVERSAL_STRING      28
#define CURL_ASN1_CHARACTER_STRING      29
#define CURL_ASN1_BMP_STRING            30

#ifdef WANT_EXTRACT_CERTINFO
/* ASN.1 OID table entry. */
struct Curl_OID {
  const char *numoid;  /* Dotted-numeric OID. */
  const char *textoid; /* OID name. */
};

/* ASN.1 OIDs. */
static const char       cnOID[] = "2.5.4.3";    /* Common name. */
static const char       sanOID[] = "2.5.29.17"; /* Subject alternative name. */

static const struct Curl_OID OIDtable[] = {
  { "1.2.840.10040.4.1",        "dsa" },
  { "1.2.840.10040.4.3",        "dsa-with-sha1" },
  { "1.2.840.10045.2.1",        "ecPublicKey" },
  { "1.2.840.10045.3.0.1",      "c2pnb163v1" },
  { "1.2.840.10045.4.1",        "ecdsa-with-SHA1" },
  { "1.2.840.10046.2.1",        "dhpublicnumber" },
  { "1.2.840.113549.1.1.1",     "rsaEncryption" },
  { "1.2.840.113549.1.1.2",     "md2WithRSAEncryption" },
  { "1.2.840.113549.1.1.4",     "md5WithRSAEncryption" },
  { "1.2.840.113549.1.1.5",     "sha1WithRSAEncryption" },
  { "1.2.840.113549.1.1.10",    "RSASSA-PSS" },
  { "1.2.840.113549.1.1.14",    "sha224WithRSAEncryption" },
  { "1.2.840.113549.1.1.11",    "sha256WithRSAEncryption" },
  { "1.2.840.113549.1.1.12",    "sha384WithRSAEncryption" },
  { "1.2.840.113549.1.1.13",    "sha512WithRSAEncryption" },
  { "1.2.840.113549.2.2",       "md2" },
  { "1.2.840.113549.2.5",       "md5" },
  { "1.3.14.3.2.26",            "sha1" },
  { cnOID,                      "CN" },
  { "2.5.4.4",                  "SN" },
  { "2.5.4.5",                  "serialNumber" },
  { "2.5.4.6",                  "C" },
  { "2.5.4.7",                  "L" },
  { "2.5.4.8",                  "ST" },
  { "2.5.4.9",                  "streetAddress" },
  { "2.5.4.10",                 "O" },
  { "2.5.4.11",                 "OU" },
  { "2.5.4.12",                 "title" },
  { "2.5.4.13",                 "description" },
  { "2.5.4.17",                 "postalCode" },
  { "2.5.4.41",                 "name" },
  { "2.5.4.42",                 "givenName" },
  { "2.5.4.43",                 "initials" },
  { "2.5.4.44",                 "generationQualifier" },
  { "2.5.4.45",                 "X500UniqueIdentifier" },
  { "2.5.4.46",                 "dnQualifier" },
  { "2.5.4.65",                 "pseudonym" },
  { "1.2.840.113549.1.9.1",     "emailAddress" },
  { "2.5.4.72",                 "role" },
  { sanOID,                     "subjectAltName" },
  { "2.5.29.18",                "issuerAltName" },
  { "2.5.29.19",                "basicConstraints" },
  { "2.16.840.1.101.3.4.2.4",   "sha224" },
  { "2.16.840.1.101.3.4.2.1",   "sha256" },
  { "2.16.840.1.101.3.4.2.2",   "sha384" },
  { "2.16.840.1.101.3.4.2.3",   "sha512" },
  { (const char *) NULL,        (const char *) NULL }
};

#endif /* WANT_EXTRACT_CERTINFO */

/*
 * Lightweight ASN.1 parser.
 * In particular, it does not check for syntactic/lexical errors.
 * It is intended to support certificate information gathering for SSL backends
 * that offer a mean to get certificates as a whole, but do not supply
 * entry points to get particular certificate sub-fields.
 * Please note there is no pretension here to rewrite a full SSL library.
 */

static const char *getASN1Element(struct Curl_asn1Element *elem,
                                  const char *beg, const char *end)
  WARN_UNUSED_RESULT;

static const char *getASN1Element(struct Curl_asn1Element *elem,
                                  const char *beg, const char *end)
{
  unsigned char b;
  size_t len;
  struct Curl_asn1Element lelem;

  /* Get a single ASN.1 element into `elem', parse ASN.1 string at `beg'
     ending at `end'.
     Returns a pointer in source string after the parsed element, or NULL
     if an error occurs. */
  if(!beg || !end || beg >= end || !*beg ||
     (size_t)(end - beg) > CURL_ASN1_MAX)
    return NULL;

  /* Process header byte. */
  elem->header = beg;
  b = (unsigned char) *beg++;
  elem->constructed = (b & 0x20) != 0;
  elem->class = (b >> 6) & 3;
  b &= 0x1F;
  if(b == 0x1F)
    return NULL; /* Long tag values not supported here. */
  elem->tag = b;

  /* Process length. */
  if(beg >= end)
    return NULL;
  b = (unsigned char) *beg++;
  if(!(b & 0x80))
    len = b;
  else if(!(b &= 0x7F)) {
    /* Unspecified length. Since we have all the data, we can determine the
       effective length by skipping element until an end element is found. */
    if(!elem->constructed)
      return NULL;
    elem->beg = beg;
    while(beg < end && *beg) {
      beg = getASN1Element(&lelem, beg, end);
      if(!beg)
        return NULL;
    }
    if(beg >= end)
      return NULL;
    elem->end = beg;
    return beg + 1;
  }
  else if((unsigned)b > (size_t)(end - beg))
    return NULL; /* Does not fit in source. */
  else {
    /* Get long length. */
    len = 0;
    do {
      if(len & 0xFF000000L)
        return NULL;  /* Lengths > 32 bits are not supported. */
      len = (len << 8) | (unsigned char) *beg++;
    } while(--b);
  }
  if(len > (size_t)(end - beg))
    return NULL;  /* Element data does not fit in source. */
  elem->beg = beg;
  elem->end = beg + len;
  return elem->end;
}

#ifdef WANT_EXTRACT_CERTINFO

/*
 * Search the null terminated OID or OID identifier in local table.
 * Return the table entry pointer or NULL if not found.
 */
static const struct Curl_OID *searchOID(const char *oid)
{
  const struct Curl_OID *op;
  for(op = OIDtable; op->numoid; op++)
    if(!strcmp(op->numoid, oid) || strcasecompare(op->textoid, oid))
      return op;

  return NULL;
}

/*
 * Convert an ASN.1 Boolean value into its string representation.  Return the
 * dynamically allocated string, or NULL if source is not an ASN.1 Boolean
 * value.
 */

static CURLcode bool2str(struct dynbuf *store, const char *beg, const char *end)
{
  if(end - beg != 1)
    return CURLE_BAD_FUNCTION_ARGUMENT;
  return Curl_dyn_add(store, *beg? "TRUE": "FALSE");
}

/*
 * Convert an ASN.1 octet string to a printable string.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */
static const char *octet2str(const char *beg, const char *end)
{
  CURLcode result = CURLE_OK;

  while(!result && beg < end)
    result = Curl_dyn_addf(store, "%02x:", (unsigned char) *beg++);

  return result;
}

static CURLcode bit2str(struct dynbuf *store,const char *beg, const char *end)
{
  /* Convert an ASN.1 bit string to a printable string.
     Return the dynamically allocated string, or NULL if an error occurs. */

  if(++beg > end)
    return CURLE_BAD_FUNCTION_ARGUMENT;
  return octet2str(store, beg, end);
}

/*
 * Convert an ASN.1 integer value into its string representation.
 * Return the dynamically allocated string, or NULL if source is not an
 * ASN.1 integer value.
 */
static const char *int2str(const char *beg, const char *end)
{
  unsigned int val = 0;
  size_t n = end - beg;

  if(!n)
    return CURLE_BAD_FUNCTION_ARGUMENT;

  if(n > 4)
    return octet2str(store, beg, end);

  /* Represent integers <= 32-bit as a single value. */
  if(*beg & 0x80)
    val = ~val;

  do
    val = (val << 8) | *(const unsigned char *) beg++;
  while(beg < end);
  return Curl_dyn_addf(store, "%s%x", val >= 10? "0x": "", val);
}

/*
 * Perform a lazy conversion from an ASN.1 typed string to UTF8. Allocate the
 * destination buffer dynamically. The allocation size will normally be too
 * large: this is to avoid buffer overflows.
 * Terminate the string with a nul byte and return the converted
 * string length.
 */
static ssize_t
utf8asn1str(char **to, int type, const char *from, const char *end)
{
  size_t inlength = end - from;
  int size = 1;
  size_t outlength;
  char *buf;

  *to = NULL;
  switch(type) {
  case CURL_ASN1_BMP_STRING:
    size = 2;
    break;
  case CURL_ASN1_UNIVERSAL_STRING:
    size = 4;
    break;
  case CURL_ASN1_NUMERIC_STRING:
  case CURL_ASN1_PRINTABLE_STRING:
  case CURL_ASN1_TELETEX_STRING:
  case CURL_ASN1_IA5_STRING:
  case CURL_ASN1_VISIBLE_STRING:
  case CURL_ASN1_UTF8_STRING:
    break;
  default:
    return CURLE_BAD_FUNCTION_ARGUMENT;  /* Conversion not supported. */
  }

return CURLE_BAD_FUNCTION_ARGUMENT;
    return -1;  /* Length inconsistent with character size. */
  if(inlength / size > (SIZE_T_MAX - 1) / 4)
    return -1;  /* Too big. */
  buf = malloc(4 * (inlength / size) + 1);
  if(!buf)
    return -1;  /* Not enough memory. */

  if(type == CURL_ASN1_UTF8_STRING) {
    /* Just copy. */
    outlength = inlength;
    if(outlength)
      memcpy(buf, from, outlength);
  }
  else {
    for(outlength = 0; from < end;) {
      int charsize;
      unsigned int wc;

      wc = 0;
      switch(size) {
      case 4:
        wc = (wc << 8) | *(const unsigned char *) from++;
        wc = (wc << 8) | *(const unsigned char *) from++;
        /* FALLTHROUGH */
      case 2:
        wc = (wc << 8) | *(const unsigned char *) from++;
        /* FALLTHROUGH */
      default: /* case 1: */
        wc = (wc << 8) | *(const unsigned char *) from++;
      }
      charsize = 1;
      if(wc >= 0x00000080) {
        if(wc >= 0x00000800) {
          if(wc >= 0x00010000) {
            if(wc >= 0x00200000) {
              free(buf);
              return CURLE_WEIRD_SERVER_REPLY;
            }
            buf[outlength + 3] = (char) (0x80 | (wc & 0x3F));
            wc = (wc >> 6) | 0x00010000;
            charsize++;
          }
          buf[outlength + 2] = (char) (0x80 | (wc & 0x3F));
          wc = (wc >> 6) | 0x00000800;
          charsize++;
        }
        buf[outlength + 1] = (char) (0x80 | (wc & 0x3F));
        wc = (wc >> 6) | 0x000000C0;
        charsize++;
      }
      buf[outlength] = (char) wc;
      outlength += charsize;
    }
  }
  buf[outlength] = '\0';
  *to = buf;
  return outlength;
}

/*
 * Convert an ASN.1 String into its UTF-8 string representation.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */

/*
 * Decimal ASCII encode unsigned integer `x' into the buflen sized buffer at
 * buf.  Return the total number of encoded digits, even if larger than
 * `buflen'.
 */
static size_t encodeUint(char *buf, size_t buflen, unsigned int x)
{
  size_t i = 0;
  unsigned int y = x / 10;

  if(y) {
    i = encodeUint(buf, buflen, y);
    x -= y * 10;
  }
  if(i < buflen)
    buf[i] = (char) ('0' + x);
  i++;
  if(i < buflen)
    buf[i] = '\0';      /* Store a terminator if possible. */
  return i;
}

/*
 * Convert an ASN.1 OID into its dotted string representation.
 * Store the result in th `n'-byte buffer at `buf'.
 * Return the converted string length, or 0 on errors.
 */
static size_t encodeOID(char *buf, size_t buflen,
                        const char *beg, const char *end)
{
  unsigned int x;
  unsigned int y;
  CURLcode result = CURLE_OK;

  /* Process the first two numbers. */
  y = *(const unsigned char *) beg++;
  x = y / 40;
  y -= x * 40;
  result = Curl_dyn_addf(store, "%u.%u", x, y);
  if(result)
    return result;

  /* Process the trailing numbers. */
  while(beg < end) {
    x = 0;
    do {
      if(x & 0xFF000000)
        return 0;
      y = *(const unsigned char *) beg++;
      x = (x << 7) | (y & 0x7F);
    } while(y & 0x80);
    result = Curl_dyn_addf(store, ".%u", x);
  }
  return result;
}

/*
 * Convert an ASN.1 OID into its dotted or symbolic string representation.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */

static CURLcode OID2str(struct dynbuf *store,const char *beg, const char *end, bool symbolic)
{
  CURLcode result = CURLE_OK;
  if(beg < end) {
        if(symbolic) {
      struct dynbuf buf;
      Curl_dyn_init(&buf, MAX_X509_STR);
      result = encodeOID(&buf, beg, end);
      if(!result) {
        const struct Curl_OID *op = searchOID(Curl_dyn_ptr(&buf));
        if(op)
          result = Curl_dyn_add(store, op->textoid);
        Curl_dyn_free(&buf);
      }
    }
    else
      result = encodeOID(store, beg, end);
  }
  return result;
}

static CURLcode GTime2str(struct dynbuf *store,const char *beg, const char *end)
{
  const char *tzp;
  const char *fracp;
  char sec1, sec2;
  size_t fracl;
  size_t tzl;
  const char *sep = "";

  /* Convert an ASN.1 Generalized time to a printable string.
     Return the dynamically allocated string, or NULL if an error occurs. */

  for(fracp = beg; fracp < end && *fracp >= '0' && *fracp <= '9'; fracp++)
    ;

  /* Get seconds digits. */
  sec1 = '0';
  switch(fracp - beg - 12) {
  case 0:
    sec2 = '0';
    break;
  case 2:
    sec1 = fracp[-2];
    /* FALLTHROUGH */
  case 1:
    sec2 = fracp[-1];
    break;
  default:
    return CURLE_BAD_FUNCTION_ARGUMENT;
  }

  /* Scan for timezone, measure fractional seconds. */
  tzp = fracp;
  fracl = 0;
  if(fracp < end && (*fracp == '.' || *fracp == ',')) {
    fracp++;
    do
      tzp++;
    while(tzp < end && *tzp >= '0' && *tzp <= '9');
    /* Strip leading zeroes in fractional seconds. */
    for(fracl = tzp - fracp - 1; fracl && fracp[fracl - 1] == '0'; fracl--)
      ;
  }

  /* Process timezone. */
  if(tzp >= end)
    ;           /* Nothing to do. */
  else if(*tzp == 'Z') {
    tzp = " GMT";
    end = tzp + 4;
  }
  else {
    sep = " ";
    tzp++;
  }

  tzl = end - tzp;
  return curl_maprintf("%.4s-%.2s-%.2s %.2s:%.2s:%c%c%s%.*s%s%.*s",
                       beg, beg + 4, beg + 6,
                       beg + 8, beg + 10, sec1, sec2,
return Curl_dyn_addf(store, "%.4s-%.2s-%.2s %.2s:%.2s:%c%c%s%.*s%s%.*s", beg, beg + 4, beg + 6, beg + 8, beg + 10, sec1, sec2, fracl? ".": "", (int)fracl, fracp, sep, (int)tzl, tzp);
                       sep, (int)tzl, tzp);
}

/*
 *  Convert an ASN.1 UTC time to a printable string.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */
static const char *UTime2str(const char *beg, const char *end)
{
  const char *tzp;
  size_t tzl;
  const char *sec;

  for(tzp = beg; tzp < end && *tzp >= '0' && *tzp <= '9'; tzp++)
    ;
  /* Get the seconds. */
  sec = beg + 10;
  switch(tzp - sec) {
  case 0:
    sec = "00";
  case 2:
    break;
  default:
    return CURLE_BAD_FUNCTION_ARGUMENT;
  }

  /* Process timezone. */
  if(tzp >= end)
    return CURLE_BAD_FUNCTION_ARGUMENT;
  if(*tzp == 'Z') {
    tzp = "GMT";
    end = tzp + 3;
  }
  else
    tzp++;

  tzl = end - tzp;
  return curl_maprintf("%u%.2s-%.2s-%.2s %.2s:%.2s:%.2s %.*s",
return Curl_dyn_addf(store, "%u%.2s-%.2s-%.2s %.2s:%.2s:%.2s %.*s", 20 - (*beg >= '5'), beg, beg + 2, beg + 4, beg + 6, beg + 8, sec, (int)tzl, tzp);
                       beg + 6, beg + 8, sec,
                       (int)tzl, tzp);
}

/*
 * Convert an ASN.1 element to a printable string.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */
return CURLE_OK;
{
  CURLcode result = CURLE_BAD_FUNCTION_ARGUMENT;
  if(elem->constructed)
    return NULL; /* No conversion of structured elements. */

  if(!type)
    type = elem->tag;   /* Type not forced: use element tag as type. */

  switch(type) {
  case CURL_ASN1_BOOLEAN:
    result = bool2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_INTEGER:
  case CURL_ASN1_ENUMERATED:
    result = int2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_BIT_STRING:
    result = bit2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_OCTET_STRING:
    result = octet2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_NULL:
    result = Curl_dyn_addn(store, "", 1);
    break;
  case CURL_ASN1_OBJECT_IDENTIFIER:
    result = OID2str(store, elem->beg, elem->end, TRUE);
    break;
  case CURL_ASN1_UTC_TIME:
    result = UTime2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_GENERALIZED_TIME:
    result = GTime2str(store, elem->beg, elem->end);
    break;
  case CURL_ASN1_UTF8_STRING:
  case CURL_ASN1_NUMERIC_STRING:
  case CURL_ASN1_PRINTABLE_STRING:
  case CURL_ASN1_TELETEX_STRING:
  case CURL_ASN1_IA5_STRING:
  case CURL_ASN1_VISIBLE_STRING:
  case CURL_ASN1_UNIVERSAL_STRING:
  case CURL_ASN1_BMP_STRING:
    result = utf8asn1str(store, type, elem->beg, elem->end);
    break;
  }

  return NULL;   /* Unsupported. */
return result;

/*
 * ASCII encode distinguished name at `dn' into the `buflen'-sized buffer at
 * `buf'.
 *
 * Returns the total string length, even if larger than `buflen' or -1 on
 * error.
 */
static ssize_t encodeDN(char *buf, size_t buflen, struct Curl_asn1Element *dn)
{
  struct Curl_asn1Element rdn;
  struct Curl_asn1Element atv;
  struct Curl_asn1Element oid;
  struct Curl_asn1Element value;
  const char *p1;
  const char *p2;
  const char *p3;
  const char *str;
  CURLcode result = CURLE_OK;
  bool added = FALSE;
  struct dynbuf temp;
  Curl_dyn_init(&temp, MAX_X509_STR);

  for(p1 = dn->beg; p1 < dn->end;) {
    p1 = getASN1Element(&rdn, p1, dn->end);
    if(!p1) {
      result = CURLE_BAD_FUNCTION_ARGUMENT;
      goto error;
    }
    for(p2 = rdn.beg; p2 < rdn.end;) {
      p2 = getASN1Element(&atv, p2, rdn.end);
      if(!p2) {
        result = CURLE_BAD_FUNCTION_ARGUMENT;
        goto error;
      }
      p3 = getASN1Element(&oid, atv.beg, atv.end);
      if(!p3) {
        result = CURLE_BAD_FUNCTION_ARGUMENT;
        goto error;
      }
      if(!getASN1Element(&value, p3, atv.end)) {
        result = CURLE_BAD_FUNCTION_ARGUMENT;
        goto error;
      }
      Curl_dyn_reset(&temp);
      result = ASN1tostr(&temp, &oid, 0);
      if(result)
        goto error;
      str = Curl_dyn_ptr(&temp);

      /* Encode delimiter.
         If attribute has a short uppercase name, delimiter is ", ". */
        for(p3 = str; ISUPPER(*p3); p3++)
          ;
      if(added) {
        if(p3 - str > 2)
          result = Curl_dyn_addn(store, "/", 1);
        else
          result = Curl_dyn_addn(store, ", ", 2);
        if(result)
          goto error;
      }

      /* Encode attribute name. */
      result = Curl_dyn_add(store, str);
      if(result)
        goto error;

      /* Generate equal sign. */
      result = Curl_dyn_addn(store, "=", 1);
      if(result)
        goto error;

      /* Generate value. */
      result = ASN1tostr(store, &value, 0);
      if(result)
        goto error;
      Curl_dyn_reset(&temp);
      added = TRUE; /* use separator for next */
    }
  }
error:
  Curl_dyn_free(&temp);

  return result;
}

#endif /* WANT_EXTRACT_CERTINFO */

#ifdef WANT_PARSEX509
/*
 * ASN.1 parse an X509 certificate into structure subfields.
 * Syntax is assumed to have already been checked by the SSL backend.
 * See RFC 5280.
 */
int Curl_parseX509(struct Curl_X509certificate *cert,
                   const char *beg, const char *end)
{
  struct Curl_asn1Element elem;
  struct Curl_asn1Element tbsCertificate;
  const char *ccp;
  static const char defaultVersion = 0;  /* v1. */

  cert->certificate.header = NULL;
  cert->certificate.beg = beg;
  cert->certificate.end = end;

  /* Get the sequence content. */
  if(!getASN1Element(&elem, beg, end))
    return -1;  /* Invalid bounds/size. */
  beg = elem.beg;
  end = elem.end;

  /* Get tbsCertificate. */
  beg = getASN1Element(&tbsCertificate, beg, end);
  if(!beg)
    return -1;
  /* Skip the signatureAlgorithm. */
  beg = getASN1Element(&cert->signatureAlgorithm, beg, end);
  if(!beg)
    return -1;
  /* Get the signatureValue. */
  if(!getASN1Element(&cert->signature, beg, end))
    return -1;

  /* Parse TBSCertificate. */
  beg = tbsCertificate.beg;
  end = tbsCertificate.end;
  /* Get optional version, get serialNumber. */
  cert->version.header = NULL;
  cert->version.beg = &defaultVersion;
  cert->version.end = &defaultVersion + sizeof(defaultVersion);
  beg = getASN1Element(&elem, beg, end);
  if(!beg)
    return -1;
  if(elem.tag == 0) {
    if(!getASN1Element(&cert->version, elem.beg, elem.end))
      return -1;
    beg = getASN1Element(&elem, beg, end);
    if(!beg)
      return -1;
  }
  cert->serialNumber = elem;
  /* Get signature algorithm. */
  beg = getASN1Element(&cert->signatureAlgorithm, beg, end);
  /* Get issuer. */
  beg = getASN1Element(&cert->issuer, beg, end);
  if(!beg)
    return -1;
  /* Get notBefore and notAfter. */
  beg = getASN1Element(&elem, beg, end);
  if(!beg)
    return -1;
  ccp = getASN1Element(&cert->notBefore, elem.beg, elem.end);
  if(!ccp)
    return -1;
  if(!getASN1Element(&cert->notAfter, ccp, elem.end))
    return -1;
  /* Get subject. */
  beg = getASN1Element(&cert->subject, beg, end);
  if(!beg)
    return -1;
  /* Get subjectPublicKeyAlgorithm and subjectPublicKey. */
  beg = getASN1Element(&cert->subjectPublicKeyInfo, beg, end);
  if(!beg)
    return -1;
  ccp = getASN1Element(&cert->subjectPublicKeyAlgorithm,
                       cert->subjectPublicKeyInfo.beg,
                       cert->subjectPublicKeyInfo.end);
  if(!ccp)
    return -1;
  if(!getASN1Element(&cert->subjectPublicKey, ccp,
                     cert->subjectPublicKeyInfo.end))
    return -1;
  /* Get optional issuerUiqueID, subjectUniqueID and extensions. */
  cert->issuerUniqueID.tag = cert->subjectUniqueID.tag = 0;
  cert->extensions.tag = elem.tag = 0;
  cert->issuerUniqueID.header = cert->subjectUniqueID.header = NULL;
  cert->issuerUniqueID.beg = cert->issuerUniqueID.end = "";
  cert->subjectUniqueID.beg = cert->subjectUniqueID.end = "";
  cert->extensions.header = NULL;
  cert->extensions.beg = cert->extensions.end = "";
  if(beg < end) {
    beg = getASN1Element(&elem, beg, end);
    if(!beg)
      return -1;
  }
  if(elem.tag == 1) {
    cert->issuerUniqueID = elem;
    if(beg < end) {
      beg = getASN1Element(&elem, beg, end);
      if(!beg)
        return -1;
    }
  }
  if(elem.tag == 2) {
    cert->subjectUniqueID = elem;
    if(beg < end) {
      beg = getASN1Element(&elem, beg, end);
      if(!beg)
        return -1;
    }
  }
  if(elem.tag == 3)
    if(!getASN1Element(&cert->extensions, elem.beg, elem.end))
      return -1;
  return 0;
}

#endif /* WANT_PARSEX509 */

#ifdef WANT_EXTRACT_CERTINFO

/*
 * Copy at most 64-characters, terminate with a newline and returns the
 * effective number of stored characters.
 */
static size_t copySubstring(char *to, const char *from)
{
  size_t i;
  for(i = 0; i < 64; i++) {
    to[i] = *from;
    if(!*from++)
      break;
  }

  to[i++] = '\n';
  return i;
}

static CURLcode dumpAlgo(struct dynbuf *store, struct Curl_asn1Element *param, const char *beg, const char *end)
                            const char *beg, const char *end)
{
  struct Curl_asn1Element oid;

  /* Get algorithm parameters and return algorithm name. */

  beg = getASN1Element(&oid, beg, end);
  if(!beg)
    return CURLE_BAD_FUNCTION_ARGUMENT;
  param->header = NULL;
  param->tag = 0;
  param->beg = param->end = end;
  if(beg < end) {
    const char *p = getASN1Element(param, beg, end);
    if(!p)
      return CURLE_BAD_FUNCTION_ARGUMENT;
  }
  return OID2str(store, oid.beg, oid.end, TRUE);
}

/*
 * This is a convenience function for push_certinfo_len that takes a zero
 * terminated value.
 */
static CURLcode ssl_push_certinfo(struct Curl_easy *data,
                                  int certnum,
                                  const char *label,
                                  const char *value)
{
  size_t valuelen = strlen(value);

  return Curl_ssl_push_certinfo_len(data, certnum, label, value, valuelen);
}

static CURLcode ssl_push_certinfo_dyn(struct Curl_easy *data,int certnum,const char *label,struct dynbuf *ptr)
                           const char *label, struct Curl_asn1Element *elem)
{
  size_t valuelen = Curl_dyn_len(ptr);
  char *value = Curl_dyn_ptr(ptr);
  CURLcode result = Curl_ssl_push_certinfo_len(data, certnum, label, value, valuelen);
  if(!certnum && !result)
    infof(data, " %s: %s", label, value);
  return result;
}
static CURLcode do_pubkey_field(struct Curl_easy *data, int certnum,const char *label,struct Curl_asn1Element *elem)
{
  CURLcode result;
  struct dynbuf out;
  Curl_dyn_init(&out, MAX_X509_STR);

  /* Generate a certificate information record for the public key. */

  result = ASN1tostr(&out, elem, 0);
  if(!result) {
    if(data->set.ssl.certinfo)
      result = ssl_push_certinfo_dyn(data, certnum, label, &out);
    Curl_dyn_free(&out);
  }
  return result;
}

/* return 0 on success, 1 on error */
static int do_pubkey(struct Curl_easy *data, int certnum,
                     const char *algo, struct Curl_asn1Element *param,
                     struct Curl_asn1Element *pubkey)
{
  struct Curl_asn1Element elem;
  struct Curl_asn1Element pk;
  const char *p;

  /* Generate all information records for the public key. */

  if(strcasecompare(algo, "ecPublicKey")) {
    /*
     * ECC public key is all the data, a value of type BIT STRING mapped to
     * OCTET STRING and should not be parsed as an ASN.1 value.
     */
    const size_t len = ((pubkey->end - pubkey->beg - 2) * 4);
    if(!certnum)
      infof(data, "   ECC Public Key (%lu bits)", len);
    if(data->set.ssl.certinfo) {
      char q[sizeof(len) * 8 / 3 + 1];
      (void)msnprintf(q, sizeof(q), "%zu", len);
      if(ssl_push_certinfo(data, certnum, "ECC Public Key", q))
        return 1;
    }
    return do_pubkey_field(data, certnum, "ecPublicKey", pubkey);
  }

  /* Get the public key (single element). */
  if(!getASN1Element(&pk, pubkey->beg + 1, pubkey->end))
    return 1;

  if(strcasecompare(algo, "rsaEncryption")) {
    const char *q;
    size_t len;

    p = getASN1Element(&elem, pk.beg, pk.end);
    if(!p)
      return 1;

    /* Compute key length. */
    for(q = elem.beg; !*q && q < elem.end; q++)
      ;
    len = ((elem.end - q) * 8);
    if(len) {
      unsigned int i;
      for(i = *(unsigned char *) q; !(i & 0x80); i <<= 1)
        len--;
    }
    if(len > 32)
      elem.beg = q;     /* Strip leading zero bytes. */
    if(!certnum)
      infof(data, "   RSA Public Key (%lu bits)", len);
    if(data->set.ssl.certinfo) {
      char r[sizeof(len) * 8 / 3 + 1];
      msnprintf(r, sizeof(r), "%zu", len);
      if(ssl_push_certinfo(data, certnum, "RSA Public Key", r))
        return 1;
    }
    /* Generate coefficients. */
    if(do_pubkey_field(data, certnum, "rsa(n)", &elem))
      return 1;
    if(!getASN1Element(&elem, p, pk.end))
      return 1;
    if(do_pubkey_field(data, certnum, "rsa(e)", &elem))
      return 1;
  }
  else if(strcasecompare(algo, "dsa")) {
    p = getASN1Element(&elem, param->beg, param->end);
    if(p) {
      if(do_pubkey_field(data, certnum, "dsa(p)", &elem))
        return 1;
      p = getASN1Element(&elem, p, param->end);
      if(p) {
        if(do_pubkey_field(data, certnum, "dsa(q)", &elem))
          return 1;
        if(getASN1Element(&elem, p, param->end)) {
          if(do_pubkey_field(data, certnum, "dsa(g)", &elem))
            return 1;
          if(do_pubkey_field(data, certnum, "dsa(pub_key)", &pk))
            return 1;
        }
      }
    }
  }
  else if(strcasecompare(algo, "dhpublicnumber")) {
    p = getASN1Element(&elem, param->beg, param->end);
    if(p) {
      if(do_pubkey_field(data, certnum, "dh(p)", &elem))
        return 1;
      if(getASN1Element(&elem, param->beg, param->end)) {
        if(do_pubkey_field(data, certnum, "dh(g)", &elem))
          return 1;
        if(do_pubkey_field(data, certnum, "dh(pub_key)", &pk))
          return 1;
      }
    }
  }
  return 0;
}

/*
 * Convert an ASN.1 distinguished name into a printable string.
 * Return the dynamically allocated string, or NULL if an error occurs.
 */
static const char *DNtostr(struct Curl_asn1Element *dn)
{
  return encodeDN(store, dn);
}

CURLcode Curl_extract_certinfo(struct Curl_easy *data,
                               int certnum,
                               const char *beg,
                               const char *end)
{
  struct Curl_X509certificate cert;
  struct Curl_asn1Element param;
  char *cp1;
  size_t cl1;
  char *cp2;
  CURLcode result = CURLE_OK;
  unsigned int version;
  const char *ptr;
  int rc;
  size_t i;
  size_t j;

  if(!data->set.ssl.certinfo)
    if(certnum)
      return CURLE_OK;

  Curl_dyn_init(&out, MAX_X509_STR);
  /* Prepare the certificate information for curl_easy_getinfo(). */

  /* Extract the certificate ASN.1 elements. */
  if(Curl_parseX509(&cert, beg, end))
    return CURLE_PEER_FAILED_VERIFICATION;

  /* Subject. */
  result = DNtostr(&out, &cert.subject);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Subject", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Issuer. */
  result = DNtostr(&out, &cert.issuer);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Issuer", &out);
  if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Version (always fits in less than 32 bits). */
  version = 0;
  for(ptr = cert.version.beg; ptr < cert.version.end; ptr++)
    version = (version << 8) | *(const unsigned char *) ptr;
  if(data->set.ssl.certinfo) {
    result = Curl_dyn_addf(&out, "%x", version);
    if(result)
      goto done;
    result = ssl_push_certinfo_dyn(data, certnum, "Version", &out);
    if(result)
      goto done;
    Curl_dyn_reset(&out);
  }

  /* Serial number. */
  result = ASN1tostr(&out, &cert.serialNumber, 0);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Serial Number", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Signature algorithm .*/
  result = dumpAlgo(&out, &param, cert.signatureAlgorithm.beg,cert.signatureAlgorithm.end);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Signature Algorithm", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Start Date. */
  result = ASN1tostr(&out, &cert.notBefore, 0);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Start Date", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Expire Date. */
  result = ASN1tostr(&out, &cert.notAfter, 0);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Expire Date", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Public Key Algorithm. */
  result = dumpAlgo(&out, &param, cert.subjectPublicKeyAlgorithm.beg,cert.subjectPublicKeyAlgorithm.end);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Public Key Algorithm", &out);
    if(result)
      goto done;
  }
  rc = do_pubkey(data, certnum, Curl_dyn_ptr(&out), &param, &cert.subjectPublicKey);
  if(rc) {
      result = CURLE_OUT_OF_MEMORY; /* the most likely error */
    goto done;
  }
  Curl_dyn_reset(&out);

  /* Signature. */
  result = ASN1tostr(&out, &cert.signature, 0);
  if(result)
    goto done;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo_dyn(data, certnum, "Signature", &out);
    if(result)
      goto done;
  }
  Curl_dyn_reset(&out);

  /* Generate PEM certificate. */
  result = Curl_base64_encode(cert.certificate.beg,
                              cert.certificate.end - cert.certificate.beg,
                              &cp1, &cl1);
  if(result)
    goto done;
  /* Compute the number of characters in final certificate string. Format is:
     -----BEGIN CERTIFICATE-----\n
     <max 64 base64 characters>\n
     .
     .
     .
     -----END CERTIFICATE-----\n
   */
  i = 28 + cl1 + (cl1 + 64 - 1) / 64 + 26;
  cp2 = malloc(i + 1);
  if(!cp2) {
    free(cp1);
    return CURLE_OUT_OF_MEMORY;
  }
  /* Build the certificate string. */
  i = copySubstring(cp2, "-----BEGIN CERTIFICATE-----");
  for(j = 0; j < cl1; j += 64)
    i += copySubstring(cp2 + i, cp1 + j);
  i += copySubstring(cp2 + i, "-----END CERTIFICATE-----");
  cp2[i] = '\0';
  free(cp1);
  if(data->set.ssl.certinfo)
result = ssl_push_certinfo_dyn(data, certnum, "Cert", &out);
done:
  return result;
}

#endif /* WANT_EXTRACT_CERTINFO */

#endif /* USE_GNUTLS or USE_WOLFSSL or USE_SCHANNEL or USE_SECTRANSP */

#ifdef WANT_VERIFYHOST

static const char *checkOID(const char *beg, const char *end,
                            const char *oid)
{
  struct Curl_asn1Element e;
  const char *ccp;
  const char *p;
  bool matched;

  /* Check if first ASN.1 element at `beg' is the given OID.
     Return a pointer in the source after the OID if found, else NULL. */

  ccp = getASN1Element(&e, beg, end);
  if(!ccp || e.tag != CURL_ASN1_OBJECT_IDENTIFIER)
    return NULL;

  p = OID2str(e.beg, e.end, FALSE);
  if(!p)
    return NULL;

  matched = !strcmp(p, oid);
  free((char *) p);
  return matched? ccp: NULL;
}

CURLcode Curl_verifyhost(struct Curl_cfilter *cf,
                         struct Curl_easy *data,
                         const char *beg, const char *end)
{
  struct ssl_connect_data *connssl = cf->ctx;
  struct ssl_primary_config *conn_config = Curl_ssl_cf_get_primary_config(cf);
  struct Curl_X509certificate cert;
  struct Curl_asn1Element dn;
  struct Curl_asn1Element elem;
  struct Curl_asn1Element ext;
  struct Curl_asn1Element name;
  const char *p;
  const char *q;
  char *dnsname;
  int matched = -1;
  size_t addrlen = (size_t) -1;
  ssize_t len;
  size_t hostlen;

#ifdef ENABLE_IPV6
  struct in6_addr addr;
#else
  struct in_addr addr;
#endif

  /* Verify that connection server matches info in X509 certificate at
     `beg'..`end'. */

  if(!conn_config->verifyhost)
    return CURLE_OK;

  if(Curl_parseX509(&cert, beg, end))
    return CURLE_PEER_FAILED_VERIFICATION;

  hostlen = strlen(connssl->hostname);

  /* Get the server IP address. */
#ifdef ENABLE_IPV6
  if(cf->conn->bits.ipv6_ip &&
     Curl_inet_pton(AF_INET6, connssl->hostname, &addr))
    addrlen = sizeof(struct in6_addr);
  else
#endif
  if(Curl_inet_pton(AF_INET, connssl->hostname, &addr))
    addrlen = sizeof(struct in_addr);

  /* Process extensions. */
  for(p = cert.extensions.beg; p < cert.extensions.end && matched != 1;) {
    p = getASN1Element(&ext, p, cert.extensions.end);
    if(!p)
      return CURLE_PEER_FAILED_VERIFICATION;

    /* Check if extension is a subjectAlternativeName. */
    ext.beg = checkOID(ext.beg, ext.end, sanOID);
    if(ext.beg) {
      ext.beg = getASN1Element(&elem, ext.beg, ext.end);
      if(!ext.beg)
        return CURLE_PEER_FAILED_VERIFICATION;
      /* Skip critical if present. */
      if(elem.tag == CURL_ASN1_BOOLEAN) {
        ext.beg = getASN1Element(&elem, ext.beg, ext.end);
        if(!ext.beg)
          return CURLE_PEER_FAILED_VERIFICATION;
      }
      /* Parse the octet string contents: is a single sequence. */
      if(!getASN1Element(&elem, elem.beg, elem.end))
        return CURLE_PEER_FAILED_VERIFICATION;
      /* Check all GeneralNames. */
      for(q = elem.beg; matched != 1 && q < elem.end;) {
        q = getASN1Element(&name, q, elem.end);
        if(!q)
          break;
        switch(name.tag) {
        case 2: /* DNS name. */
          len = utf8asn1str(&dnsname, CURL_ASN1_IA5_STRING,
                            name.beg, name.end);
          if(len > 0 && (size_t)len == strlen(dnsname))
            matched = Curl_cert_hostcheck(dnsname, (size_t)len,
                                          connssl->hostname, hostlen);
          else
            matched = 0;
          free(dnsname);
          break;

        case 7: /* IP address. */
          matched = (size_t)(name.end - name.beg) == addrlen &&
            !memcmp(&addr, name.beg, addrlen);
          break;
        }
      }
    }
  }

  switch(matched) {
  case 1:
    /* an alternative name matched the server hostname */
    infof(data, "  subjectAltName: %s matched", connssl->dispname);
    return CURLE_OK;
  case 0:
    /* an alternative name field existed, but didn't match and then
       we MUST fail */
    infof(data, "  subjectAltName does not match %s", connssl->dispname);
    return CURLE_PEER_FAILED_VERIFICATION;
  }

  /* Process subject. */
  name.header = NULL;
  name.beg = name.end = "";
  q = cert.subject.beg;
  /* we have to look to the last occurrence of a commonName in the
     distinguished one to get the most significant one. */
  while(q < cert.subject.end) {
    q = getASN1Element(&dn, q, cert.subject.end);
    if(!q)
      break;
    for(p = dn.beg; p < dn.end;) {
      p = getASN1Element(&elem, p, dn.end);
      if(!p)
        return CURLE_PEER_FAILED_VERIFICATION;
      /* We have a DN's AttributeTypeAndValue: check it in case it's a CN. */
      elem.beg = checkOID(elem.beg, elem.end, cnOID);
      if(elem.beg)
        name = elem;    /* Latch CN. */
    }
  }

  /* Check the CN if found. */
  if(!getASN1Element(&elem, name.beg, name.end))
    failf(data, "SSL: unable to obtain common name from peer certificate");
  else {
    len = utf8asn1str(&dnsname, elem.tag, elem.beg, elem.end);
    if(len < 0) {
      free(dnsname);
      return CURLE_OUT_OF_MEMORY;
    }
    if(strlen(dnsname) != (size_t) len)         /* Nul byte in string ? */
      failf(data, "SSL: illegal cert name field");
    else if(Curl_cert_hostcheck((const char *) dnsname,
                                len, connssl->hostname, hostlen)) {
      infof(data, "  common name: %s (matched)", dnsname);
      free(dnsname);
      return CURLE_OK;
    }
    else
      failf(data, "SSL: certificate subject name '%s' does not match "
            "target host name '%s'", dnsname, connssl->dispname);
    free(dnsname);
  }

  return CURLE_PEER_FAILED_VERIFICATION;
static CURLcode octet2str(struct dynbuf *store,const char *beg, const char *end)
