static int ossl_get_ssl_sockindex_index(void)
{
  static int sockindex_index = -1;
  if(sockindex_index < 0) {
    sockindex_index = SSL_get_ex_new_index(0, NULL, NULL, NULL, NULL);
  }
  return sockindex_index;
}
