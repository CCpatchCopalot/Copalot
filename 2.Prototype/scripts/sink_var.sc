@main def exec(cpgFile: String, identifier_name: String, src_line: Int, dst_line:Int, file: String): Unit = {
  importCpg(cpgFile);
  try{
    val src=cpg.identifier.filter(node=>(node.name.equals(identifier_name) && node.lineNumber.equals(Some(src_line)))).l;
    var sink = cpg.identifier.filter { node => node.name.equals(identifier_name) && node.lineNumber.exists(ln => ln < dst_line&&ln > src_line) }.l;
    sink.reachableByFlows(src).p |> s"${file}" 
  }catch{
    case e: Exception => println("Couldn't parse that file.")
  }
}