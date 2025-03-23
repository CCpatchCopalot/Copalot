import io.shiftleft.codepropertygraph.generated.nodes.* // 导入 CPG 节点类型

@main def exec(cpgFile: String, identifier_name: String, src_lines: String, dst_lines: List[Int], file: String): Unit = {
  importCpg(cpgFile)
  try {
    // 初始化一个空的 List 来存储所有符合条件的源节点
    val srcArray = src_lines.split("\\|").map(_.toInt).toList
    var src = List.empty[Identifier]

    // 筛选出所有源节点，其行号在 src_lines 列表中
    src = cpg.identifier.filter { node =>
      node.name.equals(identifier_name) &&
      node.lineNumber.exists(line => srcArray.contains(line))
    }.l

    // 如果 src 为空，则获取所有名字为 identifier_name 且行号小于 dst_lines 中任意行号的节点
    if (src.isEmpty) {
      src = cpg.identifier.filter { node =>
        node.name.equals(identifier_name) &&
        node.lineNumber.exists(line => dst_lines.exists(dst => line < dst))
      }.l
    }

    // 筛选出所有目标节点，其行号在 dst_lines 列表中
    val sink = cpg.identifier.filter { node =>
      node.name.equals(identifier_name) &&
      node.lineNumber.exists(line => dst_lines.contains(line))
    }.l

    // 查找从目标节点可达的所有源节点的数据流，并将结果输出为格式化的 JSON
    sink.reachableByFlows(src).p |> s"${file}"
  } catch {
    case e: Exception => println("Couldn't parse that file.")
  }
}