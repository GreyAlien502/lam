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
	raise Exception(f'warning {string} definition not found');

def execute(program,filename='<lam>',library=lib):
	from parse import getUndefinedVariables;

	undefinedVariables = getUndefinedVariables(program);
	variables = {
		'__builtins__': None,
		**{
			variable: library(variable)
			for variable
			in undefinedVariables
		}
	};
	exec(
		compile(
			program,
			filename,
			'eval'
		),
		variables
	);


