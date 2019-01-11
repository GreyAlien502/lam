#!/bin/env python
import re;
import ast;


def log(*a): ...
def parse(code):
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
	pprint(output);
	print_js(output);
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
	
def execute(filename,library):
	def getUndefinedVariables(node,definedVariables=[]):
		log(definedVariables);
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
	program = parse(
		open(
			filename
		)
		.read()
	);
	log(pprint(program));
	undefinedVariables = getUndefinedVariables(program);
	variables = {
		'__builtins__': None,
		**{
			variable: library(variable)
			for variable
			in undefinedVariables
		}
	};
	log('VARIABLES:');
	for key,value in variables.items():
		log((key,value));
	log('')
	exec(
		compile(
			program,
			filename,
			'eval'
		),
		variables
	);


class objFunc:
	def __init__(self,obj):
		if type(self) == type(obj):
			raise Exception(f'invalid object passed to functionize: {obj}');
		else:
			self.obj = obj;
	def __call__(self,arg):
		#print('call',self,arg,end='')
		if type(self) == type(arg):
			obj= arg.obj;
			if str == type(obj):
				try:
					out = self.obj.__getattribute__(obj);
				except:
					out = object.__getattribute__(self.obj,obj);
			elif isinstance(obj,int) or isinstance(obj,slice):
				out = self.obj.__getitem__(obj);
			elif isinstance(obj,list) or isinstance(obj,tuple):
				out = self.obj.__call__(*[argv for argv in obj ]);
			elif isinstance(obj,dict):
				out = self.obj.__call__(**{key:value for key,value in obj.items()});
			#elif tuple == type(arg):
			#	out = self.obj.__call__(*[unwrap(argv) for argv in arg[0]],**{key:unwrap(value) for key,value in arg[1].items()});
		#print('...called')
		try:
			return objFunc(out);
		except UnboundLocalError:...
		raise Exception(f'invalid {type(arg)} arg {arg} to {self.obj}');
	def __str__(self):
		return f'objFunc:{repr(self.obj)}';
	def __repr__(self):
		return str(self);
def unwrap(func):
	if type(func) == objFunc:
		return func.obj;
	else:
		return lambda arg: unwrap(func(objFunc(arg)))
class undefined:
	def __init__(self,name):
		self.__name = name;
		raise Exception(f'Undefined: {repr(self.__name)}');
	def __getattr__(self,attr):
		raise Exception(f'Undefined: {repr(self.__name)}');
def lib(string):
	class lecian(list):
		def __call__(self,*args):
			return lecian(self + lecian(args));
	def attempt(func):
		def output(arg):
			try:
				return func(arg)
			except:...;
		return output
	import operator as op;
	import importlib;
	def buildObject(string):
		if string[:1] == "'":
			return string[1:];
		try:
			return int(string);
		except:...
		try:
			return float(string);
		except:...
		raise string + ' is not specified builder function' 
	def findObject(string):
		if string[:2] == '#!':
			return lambda x: x
		def curry(f):
			return lambda x:lambda y: objFunc(f(x.obj,y.obj))
		return {
			**{name:curry(func)
				for name,func in {
					'+': op.add,
					'-': op.neg,
					'+-': op.sub,
					'*': op.mul,
					'/': op.truediv,
					'//': op.floordiv,
					'^': op.pow,
					'%': op.mod,
					'||': op.abs,
					'&': op.and_,
					'|': op.or_,
					'is': op.is_,
					'==': op.eq,
					'<': op.lt,
					'>': op.gt,
				}.items()
			},
			**{name: objFunc(func)
				for name,func in {
					'import': importlib.import_module,
					'[': lecian(),
					'space': ' ',
				}.items()
			},
			',': lambda x: objFunc(lecian([unwrap(x)])),
			'?': (lambda e: lambda a: lambda b: a if unwrap(e) else b),
			'try': attempt,
			'class': lambda x: class_
		}[string]
	try:
		return objFunc(buildObject(string));
	except:...
	try:
		return findObject(string);
	except:...
	log(f'warning {string} definition not found');
	return undefined(string);





if __name__ == '__main__':
	import sys;
	try:
		assert( sys.argv[2] == '-v' )
		log = print
	except:
		log = lambda *x:...
	execute(sys.argv[1],lib);
