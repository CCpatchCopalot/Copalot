/*************************************************************************** *_ _ _____ *Project ___| | | |_ \| | * / __| | | | |_) | | *| (__| |_| |_ <| |___ * \___|\___/|_| \_\_____| * * Copyright (C) Daniel Stenberg, <daniel@haxx.se>, et al. * * This software is licensed as described in the file COPYING, which * you should have received as part of this distribution. The terms * are also available at https://curl.se/docs/copyright.html. * * You may opt to use, copy, modify, merge, publish, distribute and/or sell * copies of the Software, and permit persons to whom the Software is * furnished to do so, under the terms of the COPYING file. * * This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY * KIND, either express or implied. * * SPDX-License-Identifier: curl * ***************************************************************************/

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

/* * Constants. */

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

/* Max sixes */

#define MAX_X509_STR  10000
#define MAX_X509_CERT 100000

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

/* * Lightweight ASN.1 parser. * In particular, it does not check for syntactic/lexical errors. * It is intended to support certificate information gathering for SSL backends * that offer a mean to get certificates as a whole, but do not supply * entry points to get particular certificate sub-fields. * Please note there is no pretension here to rewrite a full SSL library. */

static const char *getASN1Element(struct Curl_asn1Element *elem,const char *beg, const char *end)
  WARN_UNUSED_RESULT;

static const char *getASN1Element(struct Curl_asn1Element *elem,const char *beg, const char *end)
{
  unsigned char b;
  size_t len;
  struct Curl_asn1Element lelem;

  /* Get a single ASN.1 element into `elem', parse ASN.1 string at `beg' ending at `end'. Returns a pointer in source string after the parsed element, or NULL if an error occurs. */
  if(!beg || !end || beg >= end || !*beg || (size_t)(end - beg) > CURL_ASN1_MAX)
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
    /* Unspecified length. Since we have all the data, we can determine the effective length by skipping element until an end element is found. */
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

/* * Search the null terminated OID or OID identifier in local table. * Return the table entry pointer or NULL if not found. */
static const struct Curl_OID *searchOID(const char *oid)
{
  const struct Curl_OID *op;
  for(op = OIDtable; op->numoid; op++)
    if(!strcmp(op->numoid, oid) || strcasecompare(op->textoid, oid))
      return op;

  return NULL;
}

/* * Convert an ASN.1 Boolean value into its string representation.Return the * dynamically allocated string, or NULL if source is not an ASN.1 Boolean * value. */

static const char *bool2str(const char *beg, const char *end)
{
  if(end - beg != 1)
    return NULL;
  return strdup(*beg? "TRUE": "FALSE");
}

/* * Convert an ASN.1 octet string to a printable string. * Return the dynamically allocated string, or NULL if an error occurs. */
static const char *octet2str(const char *beg, const char *end)
{
  struct dynbuf buf;
  CURLcode result;

  Curl_dyn_init(&buf, 3 * CURL_ASN1_MAX + 1);
  result = Curl_dyn_addn(&buf, "", 0);

  while(!result && beg < end)
    result = Curl_dyn_addf(&buf, "%02x:", (unsigned char) *beg++);

  return Curl_dyn_ptr(&buf);
}

static const char *bit2str(const char *beg, const char *end)
{
  /* Convert an ASN.1 bit string to a printable string. Return the dynamically allocated string, or NULL if an error occurs. */

  if(++beg > end)
    return NULL;
  return octet2str(beg, end);
}

/* * Convert an ASN.1 integer value into its string representation. * Return the dynamically allocated string, or NULL if source is not an * ASN.1 integer value. */
static const char *int2str(const char *beg, const char *end)
{
  unsigned int val = 0;
  size_t n = end - beg;

  if(!n)
    return NULL;

  if(n > 4)
    return octet2str(beg, end);

  /* Represent integers <= 32-bit as a single value. */
  if(*beg & 0x80)
    val = ~val;

  do
    val = (val << 8) | *(const unsigned char *) beg++;
  while(beg < end);
  return curl_maprintf("%s%x", val >= 10? "0x": "", val);
}

/* * Convert from an ASN.1 typed string to UTF8. * * The result is stored in a dynbuf that is inited by the user of this * function. * * Return negative on error. */
static ssize_t
utf8asn1str(struct dynbuf *to, int type, const char *from, const char *end)
{
  size_t inlength = end - from;
  int size = 1;
  CURLcode result = CURLE_OK;

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

  if(inlength % size)
    return CURLE_BAD_FUNCTION_ARGUMENT;

  if(type == CURL_ASN1_UTF8_STRING) {
    /* Just copy. */
    if(inlength)
      result = Curl_dyn_addn(to, from, inlength);
  }
  else {
    while(!result && (from < end)) {
      char buf[4]; /* decode buffer */
      int charsize = 1;
      unsigned int wc = 0;

      switch(size) {
      case 4:
        wc = (wc << 8) | *(const unsigned char *) from++;
        wc = (wc << 8) | *(const unsigned char *) from++;
        FALLTHROUGH();
      case 2:
        wc = (wc << 8) | *(const unsigned char *) from++;
        FALLTHROUGH();
      default: /* case 1: */
        wc = (wc << 8) | *(const unsigned char *) from++;
      }
      if(wc >= 0x00000080) {
        if(wc >= 0x00000800) {
          if(wc >= 0x00010000) {
            if(wc >= 0x00200000) {
              free(buf);
              return CURLE_WEIRD_SERVER_REPLY;
            }
            buf[3] = (char) (0x80 | (wc & 0x3F));
            wc = (wc >> 6) | 0x00010000;
            charsize++;
          }
          buf[2] = (char) (0x80 | (wc & 0x3F));
          wc = (wc >> 6) | 0x00000800;
          charsize++;
        }
        buf[1] = (char) (0x80 | (wc & 0x3F));
        wc = (wc >> 6) | 0x000000C0;
        charsize++;
      }
      buf[0] = (char) wc;
      result = Curl_dyn_addn(to, buf, charsize);
    }
  }
  return result;
}

/* * Convert an ASN.1 String into its UTF-8 string representation. * Return the dynamically allocated string, or NULL if an error occurs. */
static const char *string2str(int type, const char *beg, const char *end)
{
  struct dynbuf buf;
  Curl_dyn_init(&buf, MAX_X509_STR);
  if(utf8asn1str(&buf, type, beg, end) < 0)
    return NULL;
  return Curl_dyn_ptr(&buf);
}

/* * Decimal ASCII encode unsigned integer `x' into the buflen sized buffer at * buf.Return the total number of encoded digits, even if larger than * `buflen'. */
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

/* * Convert an ASN.1 OID into its dotted string representation. * Store the result in th `n'-byte buffer at `buf'. * Return the converted string length, or 0 on errors. */
static size_t encodeOID(char *buf, size_t buflen,const char *beg, const char *end)
{
  size_t i;
  unsigned int x;
  unsigned int y;

  /* Process the first two numbers. */
  y = *(const unsigned char *) beg++;
  x = y / 40;
  y -= x * 40;
  i = encodeUint(buf, buflen, x);
  if(i < buflen)
    buf[i] = '.';
  i++;
  if(i >= buflen)
    i += encodeUint(NULL, 0, y);
  else
    i += encodeUint(buf + i, buflen - i, y);

  /* Process the trailing numbers. */
  while(beg < end) {
    if(i < buflen)
      buf[i] = '.';
    i++;
    x = 0;
    do {
      if(x & 0xFF000000)
        return 0;
      y = *(const unsigned char *) beg++;
      x = (x << 7) | (y & 0x7F);
    } while(y & 0x80);
    if(i >= buflen)
      i += encodeUint(NULL, 0, x);
    else
      i += encodeUint(buf + i, buflen - i, x);
  }
  if(i < buflen)
    buf[i] = '\0';
  return i;
}

/* * Convert an ASN.1 OID into its dotted or symbolic string representation. * Return the dynamically allocated string, or NULL if an error occurs. */

static const char *OID2str(const char *beg, const char *end, bool symbolic)
{
  char *buf = NULL;
  if(beg < end) {
    size_t buflen = encodeOID(NULL, 0, beg, end);
    if(buflen) {
      buf = malloc(buflen + 1); /* one extra for the zero byte */
      if(buf) {
        encodeOID(buf, buflen, beg, end);
        buf[buflen] = '\0';

        if(symbolic) {
          const struct Curl_OID *op = searchOID(buf);
          if(op) {
            free(buf);
            buf = strdup(op->textoid);
          }
        }
      }
    }
  }
  return buf;
}

static const char *GTime2str(const char *beg, const char *end)
{
  const char *tzp;
  const char *fracp;
  char sec1, sec2;
  size_t fracl;
  size_t tzl;
  const char *sep = "";

  /* Convert an ASN.1 Generalized time to a printable string. Return the dynamically allocated string, or NULL if an error occurs. */

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
    FALLTHROUGH();
  case 1:
    sec2 = fracp[-1];
    break;
  default:
    return NULL;
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
  return curl_maprintf("%.4s-%.2s-%.2s %.2s:%.2s:%c%c%s%.*s%s%.*s", beg, beg + 4, beg + 6, beg + 8, beg + 10, sec1, sec2, fracl? ".": "", (int)fracl, fracp, sep, (int)tzl, tzp);
}

/* *Convert an ASN.1 UTC time to a printable string. * Return the dynamically allocated string, or NULL if an error occurs. */
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
    FALLTHROUGH();
  case 2:
    break;
  default:
    return NULL;
  }

  /* Process timezone. */
  if(tzp >= end)
    return NULL;
  if(*tzp == 'Z') {
    tzp = "GMT";
    end = tzp + 3;
  }
  else
    tzp++;

  tzl = end - tzp;
  return curl_maprintf("%u%.2s-%.2s-%.2s %.2s:%.2s:%.2s %.*s", 20 - (*beg >= '5'), beg, beg + 2, beg + 4, beg + 6, beg + 8, sec, (int)tzl, tzp);
}

/* * Convert an ASN.1 element to a printable string. * Return the dynamically allocated string, or NULL if an error occurs. */
static const char *ASN1tostr(struct Curl_asn1Element *elem, int type)
{
  if(elem->constructed)
    return NULL; /* No conversion of structured elements. */

  if(!type)
    type = elem->tag;   /* Type not forced: use element tag as type. */

  switch(type) {
  case CURL_ASN1_BOOLEAN:
    return bool2str(elem->beg, elem->end);
  case CURL_ASN1_INTEGER:
  case CURL_ASN1_ENUMERATED:
    return int2str(elem->beg, elem->end);
  case CURL_ASN1_BIT_STRING:
    return bit2str(elem->beg, elem->end);
  case CURL_ASN1_OCTET_STRING:
    return octet2str(elem->beg, elem->end);
  case CURL_ASN1_NULL:
    return strdup("");
  case CURL_ASN1_OBJECT_IDENTIFIER:
    return OID2str(elem->beg, elem->end, TRUE);
  case CURL_ASN1_UTC_TIME:
    return UTime2str(elem->beg, elem->end);
  case CURL_ASN1_GENERALIZED_TIME:
    return GTime2str(elem->beg, elem->end);
  case CURL_ASN1_UTF8_STRING:
  case CURL_ASN1_NUMERIC_STRING:
  case CURL_ASN1_PRINTABLE_STRING:
  case CURL_ASN1_TELETEX_STRING:
  case CURL_ASN1_IA5_STRING:
  case CURL_ASN1_VISIBLE_STRING:
  case CURL_ASN1_UNIVERSAL_STRING:
  case CURL_ASN1_BMP_STRING:
    return string2str(type, elem->beg, elem->end);
  }

  return NULL;   /* Unsupported. */
}

/* * ASCII encode distinguished name at `dn' into the `buflen'-sized buffer at * `buf'. * * Returns the total string length, even if larger than `buflen' or -1 on * error. */
static ssize_t encodeDN(char *buf, size_t buflen, struct Curl_asn1Element *dn)
{
  struct Curl_asn1Element rdn;
  struct Curl_asn1Element atv;
  struct Curl_asn1Element oid;
  struct Curl_asn1Element value;
  size_t l = 0;
  const char *p1;
  const char *p2;
  const char *p3;
  const char *str;

  for(p1 = dn->beg; p1 < dn->end;) {
    p1 = getASN1Element(&rdn, p1, dn->end);
    if(!p1)
      return -1;
    for(p2 = rdn.beg; p2 < rdn.end;) {
      p2 = getASN1Element(&atv, p2, rdn.end);
      if(!p2)
        return -1;
      p3 = getASN1Element(&oid, atv.beg, atv.end);
      if(!p3)
        return -1;
      if(!getASN1Element(&value, p3, atv.end))
        return -1;
      str = ASN1tostr(&oid, 0);
      if(!str)
        return -1;

      /* Encode delimiter. If attribute has a short uppercase name, delimiter is ", ". */
      if(l) {
        for(p3 = str; ISUPPER(*p3); p3++)
          ;
        for(p3 = (*p3 || p3 - str > 2)? "/": ", "; *p3; p3++) {
          if(l < buflen)
            buf[l] = *p3;
          l++;
        }
      }

      /* Encode attribute name. */
      for(p3 = str; *p3; p3++) {
        if(l < buflen)
          buf[l] = *p3;
        l++;
      }
      free((char *) str);

      /* Generate equal sign. */
      if(l < buflen)
        buf[l] = '=';
      l++;

      /* Generate value. */
      str = ASN1tostr(&value, 0);
      if(!str)
        return -1;
      for(p3 = str; *p3; p3++) {
        if(l < buflen)
          buf[l] = *p3;
        l++;
      }
      free((char *) str);
    }
  }

  return l;
}

#endif /* WANT_EXTRACT_CERTINFO */

#ifdef WANT_PARSEX509
/* * ASN.1 parse an X509 certificate into structure subfields. * Syntax is assumed to have already been checked by the SSL backend. * See RFC 5280. */
int Curl_parseX509(struct Curl_X509certificate *cert, const char *beg, const char *end)
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
  ccp = getASN1Element(&cert->subjectPublicKeyAlgorithm, cert->subjectPublicKeyInfo.beg, cert->subjectPublicKeyInfo.end);
  if(!ccp)
    return -1;
  if(!getASN1Element(&cert->subjectPublicKey, ccp, cert->subjectPublicKeyInfo.end))
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

static const char *dumpAlgo(struct Curl_asn1Element *param,const char *beg, const char *end)
{
  struct Curl_asn1Element oid;

  /* Get algorithm parameters and return algorithm name. */

  beg = getASN1Element(&oid, beg, end);
  if(!beg)
    return NULL;
  param->header = NULL;
  param->tag = 0;
  param->beg = param->end = end;
  if(beg < end)
    if(!getASN1Element(param, beg, end))
      return NULL;
  return OID2str(oid.beg, oid.end, TRUE);
}

/* * This is a convenience function for push_certinfo_len that takes a zero * terminated value. */
static CURLcode ssl_push_certinfo(struct Curl_easy *data,int certnum,const char *label,const char *value)
{
  size_t valuelen = strlen(value);

  return Curl_ssl_push_certinfo_len(data, certnum, label, value, valuelen);
}

/* return 0 on success, 1 on error */
static int do_pubkey_field(struct Curl_easy *data, int certnum, const char *label, struct Curl_asn1Element *elem)
{
  const char *output;
  CURLcode result = CURLE_OK;

  /* Generate a certificate information record for the public key. */

  output = ASN1tostr(elem, 0);
  if(output) {
    if(data->set.ssl.certinfo)
      result = ssl_push_certinfo(data, certnum, label, output);
    if(!certnum && !result)
      infof(data, " %s: %s", label, output);
    free((char *) output);
  }
  return result ? 1 : 0;
}

/* return 0 on success, 1 on error */
static int do_pubkey(struct Curl_easy *data, int certnum, const char *algo, struct Curl_asn1Element *param, struct Curl_asn1Element *pubkey)
{
  struct Curl_asn1Element elem;
  struct Curl_asn1Element pk;
  const char *p;

  /* Generate all information records for the public key. */

  if(strcasecompare(algo, "ecPublicKey")) {
    /* * ECC public key is all the data, a value of type BIT STRING mapped to * OCTET STRING and should not be parsed as an ASN.1 value. */
    const size_t len = ((pubkey->end - pubkey->beg - 2) * 4);
    if(!certnum)
      infof(data, " ECC Public Key (%zu bits)", len);
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
      infof(data, " RSA Public Key (%zu bits)", len);
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

/* * Convert an ASN.1 distinguished name into a printable string. * Return the dynamically allocated string, or NULL if an error occurs. */
static const char *DNtostr(struct Curl_asn1Element *dn)
{
  char *buf = NULL;
  ssize_t buflen = encodeDN(NULL, 0, dn);

  if(buflen >= 0) {
    buf = malloc(buflen + 1);
    if(buf) {
      if(encodeDN(buf, buflen + 1, dn) == -1) {
        free(buf);
        return NULL;
      }
      buf[buflen] = '\0';
    }
  }
  return buf;
}

CURLcode Curl_extract_certinfo(struct Curl_easy *data, int certnum, const char *beg, const char *end)
{
  struct Curl_X509certificate cert;
  struct Curl_asn1Element param;
  const char *ccp;
  char *certptr;
  size_t clen;
  struct dynbuf out;
  CURLcode result = CURLE_OK;
  unsigned int version;

  if(!data->set.ssl.certinfo)
    if(certnum)
      return CURLE_OK;

  /* Prepare the certificate information for curl_easy_getinfo(). */

  /* Extract the certificate ASN.1 elements. */
  if(Curl_parseX509(&cert, beg, end))
    return CURLE_PEER_FAILED_VERIFICATION;

  /* Subject. */
  ccp = DNtostr(&cert.subject);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo(data, certnum, "Subject", ccp);
    if(result)
      return result;
  }
  if(!certnum)
    infof(data, "%2d Subject: %s", certnum, ccp);
  free((char *) ccp);

  /* Issuer. */
  ccp = DNtostr(&cert.issuer);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo) {
    result = ssl_push_certinfo(data, certnum, "Issuer", ccp);
  }
  if(!certnum)
    infof(data, " Issuer: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Version (always fits in less than 32 bits). */
  version = 0;
  for(ccp = cert.version.beg; ccp < cert.version.end; ccp++)
    version = (version << 8) | *(const unsigned char *) ccp;
  if(data->set.ssl.certinfo) {
    ccp = curl_maprintf("%x", version);
    if(!ccp)
      return CURLE_OUT_OF_MEMORY;
    result = ssl_push_certinfo(data, certnum, "Version", ccp);
    free((char *) ccp);
    if(result)
      return result;
  }
  if(!certnum)
    infof(data, " Version: %u (0x%x)", version + 1, version);

  /* Serial number. */
  ccp = ASN1tostr(&cert.serialNumber, 0);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Serial Number", ccp);
  if(!certnum)
    infof(data, " Serial Number: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Signature algorithm .*/
  ccp = dumpAlgo(&param, cert.signatureAlgorithm.beg, cert.signatureAlgorithm.end);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Signature Algorithm", ccp);
  if(!certnum)
    infof(data, " Signature Algorithm: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Start Date. */
  ccp = ASN1tostr(&cert.notBefore, 0);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Start Date", ccp);
  if(!certnum)
    infof(data, " Start Date: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Expire Date. */
  ccp = ASN1tostr(&cert.notAfter, 0);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Expire Date", ccp);
  if(!certnum)
    infof(data, " Expire Date: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Public Key Algorithm. */
  ccp = dumpAlgo(&param, cert.subjectPublicKeyAlgorithm.beg, cert.subjectPublicKeyAlgorithm.end);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Public Key Algorithm",ccp);
  if(!result) {
    int ret;
    if(!certnum)
      infof(data, " Public Key Algorithm: %s", ccp);
    ret = do_pubkey(data, certnum, ccp, &param, &cert.subjectPublicKey);
    if(ret)
      result = CURLE_OUT_OF_MEMORY; /* the most likely error */
  }
  free((char *) ccp);
  if(result)
    return result;

  /* Signature. */
  ccp = ASN1tostr(&cert.signature, 0);
  if(!ccp)
    return CURLE_OUT_OF_MEMORY;
  if(data->set.ssl.certinfo)
    result = ssl_push_certinfo(data, certnum, "Signature", ccp);
  if(!certnum)
    infof(data, " Signature: %s", ccp);
  free((char *) ccp);
  if(result)
    return result;

  /* Generate PEM certificate. */
  result = Curl_base64_encode(cert.certificate.beg,cert.certificate.end - cert.certificate.beg,&certptr, &clen);
  if(result)
    return result;

  /* Generate the final output certificate string. Format is: -----BEGIN CERTIFICATE-----\n <max 64 base64 characters>\n . . . -----END CERTIFICATE-----\n */

  Curl_dyn_init(&out, MAX_X509_CERT);

  /* Build the certificate string. */
  result = Curl_dyn_add(&out, "-----BEGIN CERTIFICATE-----\n");
  if(!result) {
    size_t j = 0;

    while(!result && (j < clen)) {
      size_t chunksize = (clen - j) > 64 ? 64 : (clen - j);
      result = Curl_dyn_addn(&out, &certptr[j], chunksize);
      if(!result)
        result = Curl_dyn_addn(&out, "\n", 1);
      j += chunksize;
    }
    if(!result)
      result = Curl_dyn_add(&out, "-----END CERTIFICATE-----\n");
  }
  free(certptr);
  if(!result) {
    if(data->set.ssl.certinfo)
      result = ssl_push_certinfo(data, certnum, "Cert", Curl_dyn_ptr(&out));
    if(!certnum)
      infof(data, "%s", Curl_dyn_ptr(&out));
  }
  Curl_dyn_free(&out);
  return result;
}

#endif /* WANT_EXTRACT_CERTINFO */

#endif /* USE_GNUTLS or USE_WOLFSSL or USE_SCHANNEL or USE_SECTRANSP */
