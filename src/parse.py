import re;
import ast;

def nullog(*a):...;
def parse_code(code,log=False):
	log = print if log else nullog;
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

	class Rule:
		def __init__(self,classes,combinor):
			self.classes = classes;
			self.combinor = combinor;
		def __len__(self):
			return len(self.classes);
		def __call__(self,*matches):
			#verify everything
			for class_,match in zip(self.classes,matches):
				assert class_ == type(match), "Rule doesn't apply";
			return self.combinor(*matches);

	rules = [Rule(*rule) for rule in [
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
	] ];


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
	
	output = parse(output,rules,log);

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


def parse(tokens,rules,log=lambda*x:x):
	def reduce(rules,nodes):
		for i in range(len(nodes)):
			for rule in rules:
				try:
					#verify everything
					matches = nodes[i:i+len(rule)];
					nuvonode = rule(*matches);
					for match in matches:
						nodes.remove(match);
					nodes.insert(i,nuvonode);
					return True;
				except Exception as e:
					log(rule, i, e)
					continue;
		return False;
	while reduce(rules,tokens):
		log('reducit');
		for put in tokens:
			log('\t',put);
	return tokens;


def parse_args(args,switches=[],options=[],log=False):
	log = print if log else nullog;
	class Option:
		def __init__(self,options):
			self.options = options;
		def __len__(self):
			return 3;
		def __call__(self,options,switch,value):
			assert isinstance(options,dict);
			if switch in self.options:
				return {
					**options,
					self.options[0]: value,
				};
			raise Exception('does not apply');
	class Switch(Option):
		def __init__(self,options):
			self.options = options;
		def __len__(self):
			return 2;
		def __call__(self,options,switch):
			return Option.__call__(self,options,switch,True);
	options,*args = parse(
		[{ switch[0]: False for switch in switches }] +args,
		[ Switch(switch) for switch in switches]
		+
		[ Option(option) for option in options ],
		log
	);
	log(options);
	if len(args) > 0:
		if args[0] == '--':
			args = args[1:];
		elif args[0][:1] == '-':
			raise Exception(f'invalid argument or missing parameter: {args[0]}');
	return (options, args);
