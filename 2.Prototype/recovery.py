import difflib
import clang.cindex as clang

class CodeMapper:
    def __init__(self, original_code, transformed_code):
        self.original_code = original_code
        self.transformed_code = transformed_code
        self.original_statements = self.extract_statements(original_code)
        self.transformed_statements = self.extract_statements(transformed_code)
        self.statement_map = self.map_statements()
    
    def extract_statements(self, code):
        index = clang.Index.create()
        tu = index.parse('tmp.c', args=['-xc', '-std=c99'], unsaved_files=[('tmp.c', code)], options=0)
        statements = []
        
        def visit(node):
            if node.kind.is_statement():
                statements.append((node.extent.start.line, node.spelling or node.kind.name))
            for child in node.get_children():
                visit(child)
        
        visit(tu.cursor)
        return statements
    
    def map_statements(self):
        matcher = difflib.SequenceMatcher(None, self.original_statements, self.transformed_statements)
        mapping = {}
        
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'equal':
                for orig, trans in zip(self.original_statements[i1:i2], self.transformed_statements[j1:j2]):
                    mapping[orig] = trans
            elif opcode == 'replace':
                for orig, trans in zip(self.original_statements[i1:i2], self.transformed_statements[j1:j2]):
                    mapping[orig] = trans
            elif opcode == 'delete':
                for orig in self.original_statements[i1:i2]:
                    mapping[orig] = None
            elif opcode == 'insert':
                for trans in self.transformed_statements[j1:j2]:
                    mapping[None] = trans
        
        return mapping
    
    def mapping(self):
        return self.statement_map

    def transform_to_original(self, new_code):
        new_statements = self.extract_statements(new_code)
        reverse_map = {v: k for k, v in self.statement_map.items() if v is not None}
        transformed_statements = [reverse_map.get(stmt, stmt) for stmt in new_statements]
        
        return "\n".join([stmt[1] for stmt in transformed_statements])