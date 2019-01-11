import ast

def pprint(node):
	if type(node) == ast.Expression:
		return f'{pprint(node.body)}';
	if type(node) == ast.Call:
		return f'({pprint(node.func)} {pprint(node.args[0])})';
	if type(node) == ast.Lambda:
		return f'{node.args.args[0].arg}:{pprint(node.body)}';
	if type(node) == ast.Name:
		return f'{node.id}';
	return str(type(node));
def print_js(node):
	if type(node) == ast.Expression:
		return f'{print_js(node.body)}';
	if type(node) == ast.Call:
		return f'{print_js(node.func)}({print_js(node.args[0])})';
	if type(node) == ast.Lambda:
		return f'({node.args.args[0].arg}=>{print_js(node.body)})';
	if type(node) == ast.Name:
		return f'{node.id}';
	return str(type(node));
