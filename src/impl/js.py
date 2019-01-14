import ast;
from parse import getUndefinedVariables;
from binascii import hexlify;
import json;


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

def objFunc(string):
	return f'objFunc({string})';
def lib(string=None):
	if string == None:
		return '''
			var inner = Symbol();
			var objFunc = myObj => {
				var output = arg => {
					if( arg === inner ){ return myObj; }
					let obj = arg(inner);
					if( obj === undefined ){
						throw `invalid input ${arg}`;
					}
					if( ['string','number','symbol'].includes(typeof obj) ){
						output = myObj[obj];
						if( typeof output == 'function' ){
							output = output.bind(myObj);
						}
					}else if( true ){
						output = myObj(myObj,...obj);
					}else{
						throw `invalid input ${arg}`;
					}
					return objFunc(output);
				};
				output[inner] = inner;
				return output;
			};
			var unwrap = func => 
				func[inner] === inner?
					func(inner):
					arg => unwrap(func(objFunc(arg)))
			;
			class lecian extends Array{
				call(me,...next){
					return this.concat(next);
				}
			}
		''';
	if string[:1] == "'":
		return objFunc(json.dumps(string[1:]));
	try:
		return objFunc(json.dumps( int(string) ));
	except:...;
	try:
		return objFunc(json.dumps( float(string) ));
	except:...;
	return {
		**{
			op: f'(x=>objFunc({op} unwrap(x)))'
			for op in [
				'!','-','typeof','void'
			]
		},
		**{
			op: f'(x=>y=>objFunc(unwrap(x) {op} unwrap(y)))'
			for op in [
				'+','+-','*','/','%',
				'==','===','!=','>','<','>=','<=',
				'&&','||',
				'&','|','~','^','<<','>>',
				'in','instanceof',
			]
		},
		'[':'objFunc(new lecian())',
		'?':'(x=>y=>z=>(unwrap(x)?y:z))',
		'window':'objFunc(global)',
		'1': 'objFunc(alert)',
		',': '(x=>objFunc([unwrap(x)]))',
	}[string];

def esc(identifier):
	return '$'+hexlify(identifier.encode()).decode();
def print_js(node,library=lib):
	print(getUndefinedVariables(node));
	return ''.join([
		'(()=>{',
		lib(),
		''.join(
			f'{esc(undefined)}={lib(undefined)};'
			for undefined in getUndefinedVariables(node)
		),
		print_node(node),
		'})();'
	]);
def print_node(node):

	if type(node) == ast.Expression:
		return f'{print_node(node.body)}';
	if type(node) == ast.Call:
		return f'{print_node(node.func)}({print_node(node.args[0])})';
	if type(node) == ast.Lambda:
		return f'({esc(node.args.args[0].arg)}=>{print_node(node.body)})';
	if type(node) == ast.Name:
		return f'{esc(node.id)}';
	return str(type(node));
