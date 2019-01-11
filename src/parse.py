import re;
import ast;

def parse(code,log=False):
	if log:
		log = print
	else:
		def log(*a):...;

	def reduce(rules,tree):
		for i in range(len(tree)):
			for rule in rules:
				try:
					#verify everything
					matches = tree[i:i+len(rule[0])];
					for class_,match in zip(rule[0],matches):
						assert class_ == type(match), "Rule doesn't apply";

					nuvonode = rule[1](*matches);
					for match in matches:
						tree.remove(match);
					tree.insert(i,nuvonode);
					return True;
				except Exception as e:
					log(rule[0], i, e)
					continue;
		return False;

	def Lambda(argument):
		return ast.Lambda(
			args=ast.arguments(
				args=[ast.arg(arg=argument, annotation=None)],
				vararg=None,
				kwonlyargs=[],
				kw_defaults=[],
				kwarg=None,
				defaults=[]
			),
			body=None
		)
	def Name(name):
		return ast.Name(
			id=name,
			ctx=ast.Load()
		)
	def Call(e1,e2):
		return ast.Call(
			func=e1,
			args=[e2],
			keywords=[]
		);
	def identifier(name,lineno,col_offset):
		if len(name) !=0 and name[-1] == ':':
			output = Unbound(name[:-1]);
			node = output.lam;

		else:
			output = ast.Expression( Name(name) );
			node = output.body;
		node.lineno = lineno;
		node.col_offset = col_offset
		return output
	class Unbound:
		def __init__(self,argument):
			self.lam = Lambda(argument);
			self.expression = ast.Expression(self.lam);
		def beApplied(self,expression):
			self.lam.body = expression.body;
			return self.expression;
		def apply(self,expression):
			self.expression = ast.Expression( Call(expression.body,self.expression.body) );
			return self;
		def combine(self,unbound):
			self.lam.body = unbound.expression.body;
			self.lam = unbound.lam;
			return self;
	class Indent():
		pass;
	class Outdent():
		pass;

	rules = [
		(
			[ ast.Expression, ast.Expression ],
			lambda e1,e2: ast.Expression(Call(e1.body,e2.body)),
		),(
			[ Unbound, ast.Expression ],
			lambda u,e: u.beApplied(e),
		),(
			[ ast.Expression, Unbound ],
			lambda  e,u: u.apply(e),
		),(
			[ Unbound, Unbound ],
			lambda u1,u2: u1.combine(u2),
		),(
			[ Indent, ast.Expression, Outdent ],
			lambda opn,e,clos: e,
		),(
			[ Indent, Unbound, Outdent ],
			lambda opn,u,clos: u,
		),
	];
	#Actual code starts here:

	lines = code.split('\n');
	indents = [-1];
	output = [];
	for i in range(len(lines)):
		line = lines[i];
		tokens = [ identifier(line[match.start():match.end()],i+1,match.start()) for match in re.finditer(r'[^\s:]*\S',line) ]
		if( len(tokens) == 0 ): continue;

		indents.append( len(re.findall('^\t*',line)[0]) );
		output += (
			[Outdent() for i in range(1 - indents[-1] + indents[-2])] +
			[Indent()] +
			tokens
		);
		log(indents);
		log(line);
		log(''.join( str(type(token)) for token in output));
	output += [Outdent() for i in range(1 +indents[-1])];
	while reduce(rules,output):
		log('reducit');
		for put in output:
			log('\t',put);
		pass;
	assert len(output) == 1;
	output = output[0];
	output.lineno = 0;
	output.col_offset = 0;
	def fix_missing_locations(node):
		children = list(ast.iter_child_nodes(node))
		for child in children:
			fix_missing_locations(child)
		if len(children)>0:
			ast.copy_location(children[0],node)
	fix_missing_locations(output);
	ast.fix_missing_locations(output);
	return output;

def getUndefinedVariables(node,definedVariables=[]):
	if( type(node) == list ):
		if len(node) == 0: return [];
		return getUndefinedVariables(node[0],definedVariables);
	if( type(node) == ast.Name ):
		if node.id not in definedVariables:
			return {node.id};
		else:
			return set();
	if( type(node) == ast.Lambda ): 
		definedVariables = definedVariables + [node.args.args[0].arg];
	return set.union(
		set(),
		*[
			getUndefinedVariables(
				child,
				definedVariables
			)
			for child in ast.iter_child_nodes(node)
		]
	);
