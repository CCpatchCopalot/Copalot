void Curl_detach_connnection(struct Curl_easy *data)
{
  struct connectdata *conn = data->conn;
  if(conn)
    Curl_llist_remove(&conn->easyq, &data->conn_queue, NULL);
  data->conn = NULL;
}
