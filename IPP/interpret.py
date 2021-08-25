import sys
import xml.etree.ElementTree as ET

def var_exist(varname):
	#kontrola jestli zadana promenna existuje
	#rozdeleni promenne na nazev a ramec
	#po nalezeni promenne vrací zaznam ze slovniku obsahujici typ a hodnotu 
	varpart=str(varname).split("@")
	if(varpart[0]=='GF'):
		if(varpart[1] in GF):
			return GF[varpart[1]]
		else:
			exit(54)
	elif(varpart[0]=='LF'):
		if(LF!=None and len(LF)>0):
			if(varpart[1] in LF[-1]):
				return LF[-1][varpart[1]]
		else:
			exit(55)
	elif(varpart[0]=='TF'):
		if(TF!=None):
			if(varpart[1] in TF):
				return TF[varpart[1]]
		else:
			exit(55)
	else:
		exit(55)
	exit(54)
def label_finder():
	#projde vsechny instrukce a vyhleda labely
	#pokud nalezne label prida jeho nazev a polohu do slovniku labelu
	#dale kontroluje jestli nechyby nejaka instrukce podle attributu 'order' 
	counter=0
	for instrukce in content:
		if(instrukce.attrib['opcode']=='LABEL'):
			if instrukce[0].attrib['type']!='label':
				exit(32)
			if instrukce[0].text in Labels.keys():
				exit(52)
			Labels[instrukce[0].text]=counter
		if(int(instrukce.attrib['order'])!=counter+1):
			exit(32)
		counter=counter+1

def Sort_Tag(instrukce):
	#seradi argumenty instrukce a vyhleda prebytecny text mezi tagy
	pocet_tagu=len(list(instrukce.getchildren()));
	#kontrola prebytecneho textu a potomku
	for arg in list(instrukce.getchildren()):
		if(len(arg.attrib)!=1):
			exit(32)
		if(arg.tail):
			for char in arg.tail:
				if(char.isprintable() and ord(char)!=32):
					exit(32)
		if (arg.getchildren()!=[]):
			exit(32)
	#serazeni tagu
	if(pocet_tagu>0 and instrukce[0].tag!='arg1'):
		if(pocet_tagu>1 and instrukce[1].tag=='arg1'):
			instrukce[0],instrukce[1]=instrukce[1],instrukce[0]
		elif(pocet_tagu==3 and instrukce[2].tag=='arg1'):
			instrukce[0],instrukce[2]=instrukce[2],instrukce[0]	
		else:
			exit(32)
	if(pocet_tagu>1 and instrukce[1].tag!='arg2'):
		if(instrukce[1].getchildren()!=[]):
			exit(32)
		if(pocet_tagu>2 and instrukce[2].tag=='arg2'):
			instrukce[1],instrukce[2]=instrukce[2],instrukce[1]
		else:
			exit(32)
	if(pocet_tagu==3 and instrukce[2].tag!='arg3'):
			exit(32)


SourceArg=False
InputArg=False
StatsArg=False
StatsArgs_List=list()
#kontrola argumentu
for arg in sys.argv[1:]:
	if(arg=="--help"):
		print("Skript načte XML reprezentaci programu a tento program interpretuje"
		+"\nSpusteni:\n"
		+"	python3 interpret.py [argumenty]\n"			
		+"Argumenty:\n"
		+"	--help - vypise tuto napovedu\n"
		+"	--source=(path) - vstupni soubor s XML reprezentaci programu\n"
		+"	--input=(path) - soubor se vstupy pro samotnou interpretaci zadaného zdrojového kódu.\n"
		+"	Alespoň jeden z argumentu --source nebo --input musi byt vzdy zadan.\n"
		+"	Pokud jeden z nich chybi, tak jsou odpovidajici data nacitana ze standardniho vstupu.\n")
		exit(0)
	elif(arg.startswith('--source=')):
		SourceArg=True
		try:
			file=open(arg[9:],'r')
		except FileNotFoundError:
			exit(10)
	elif(arg.startswith('--input=')):
		InputArg=True
		try:
			Inputfile=open(arg[8:],'r')
		except FileNotFoundError:
			exit(10)
	elif(arg.startswith('--stats=')):
		StatsArg=True
		Statsfile=open(arg[8:],'w')
	elif(arg.startswith('--insts')):
		StatsArgs_List.append(1)
	elif(arg.startswith('--vars')):
		StatsArgs_List.append(2)
	else:
		exit(10)
if(SourceArg==False and InputArg==False):
	exit(10)

if(len(StatsArgs_List)>0 and StatsArg==False):
	exit(10)


if(SourceArg==False):
	file=sys.stdin

content=file.read()
try:
	content=ET.fromstring(content)
except ET.ParseError:
	exit(31)	
#slovniky promennych podle ramcu
GF={}
TF=None
LF=None
#pocet vytvorenych ramcu a kontrola aktualniho ramce
FrameCount=0
ThisFrame=0
#seznam hodnot v zasobniku
Stack=list()
#slovnik pro navesti obsahujici nazev a pozici
Labels={}
#bool jestli se ma postoupit na dalsi instrukci v poradi
#nebo byl proveden skok napriklad pomoci instrukci JUMP, CALL
next_instr=True
#nasledujici instrukce kterou program provede
active_instr=0
#zasobnik volani instrukce CALL aby instrukce RETURN vedela kam se vratit
CallStack=list()

stat_instrCount=0
stat_varcount=0

#kontrola poctu argumentu tagu 'program', prebytecneho textu a attributu
if(len(content.attrib)<1 or len(content.attrib)>3 ):
		exit(32)
if(content.text is not None):
	for char in content.text:
		if(char.isprintable() and ord(char)!=32):
			exit(32)
if(content.attrib['language']!='IPPcode19'):
	exit(32)
#serazeni instrukci podle attributu 'order'
content=sorted(content, key=lambda child: (child.tag,int(child.get('order'))))

label_finder()#projde instrukce programu a vyhleda labels

#hlavni cyklus interpretu
while(active_instr<=len(content)-1):
	stat_instrCount+=1;
	instrukce=content[active_instr]
	Arg_count=len(list(instrukce.getchildren()))

	#kontrola prebytecneho textu mezi tagy a attributu
	if(instrukce.text is not None):
		for char in instrukce.text:
			if(char.isprintable() and ord(char)!=32):
				exit(32)
	if(len(instrukce.attrib)!=2):
		exit(32)
	if('order' in instrukce.attrib and 'opcode' in instrukce.attrib):
		pass
	else:
		exit(32)
	#serazeni potomku instrukce
	Sort_Tag(instrukce)

	#prevedeni nazvu instrukce na velke pismena protoze jsou case-insensitive
	instrukce.attrib['opcode']=instrukce.attrib['opcode'].upper()
	#vyhledani instrukce pomoci attribudu 'opcode' kontrola spravneho poctu argumentu
	if(instrukce.attrib['opcode']=='DEFVAR' and Arg_count==1):
		stat_varcount+=1;
		#rozdeleni promene na nazev a ramec
		varpart=str(instrukce[0].text).split('@')
		if(instrukce[0].attrib['type']=='var'):
			if(varpart[0]=='GF'):#inicializace promenne
				GF[varpart[1]]={}#jeji pridani do slovniku ramce a nastaveni vychozich hodnot
				GF[varpart[1]]['type']='exist'
				GF[varpart[1]]['val']=None
			elif(varpart[0]=='TF'):
				if(TF!=None):
					TF[varpart[1]]={}
					TF[varpart[1]]['type']='exist'
					TF[varpart[1]]['val']=None
				else:
					exit(55)
			elif(varpart[0]=='LF'):
				if(LF!=None and len(LF)>0):
					LF[-1][varpart[1]]={}
					LF[-1][varpart[1]]['type']='exist'
					LF[-1][varpart[1]]['val']=None
				else:
					exit(55)
			else:
				exit(32)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='MOVE' and Arg_count==2):

		newtype=instrukce[1].attrib['type']
		newval=instrukce[1].text
		if(newtype=='var'):
			var=var_exist(instrukce[1].text)
			newtype=var['type']
			newval=var['val']
		elif(newtype=='string'):
			if newval is not None:#kontrola jestli string neobsahuje nepovoleny znak
				if '#' in newval:
					exit(32)
			if(newval is None):
				newval=''
			stringpart=str(newval).split('\\')
			newstring=''
			for part in stringpart:
				part="\\"+part
				#kontrola jestli zacatek casti stringu neobsahuje escape sequenci
				if(part[1:4].isdigit() and len(part[1:4])==3):
					#nahrazeni escape sequence znakem
					part=part.replace(part[:4],chr(int(part[1:4])))
				else:
					part=part[1:]

				newstring+=part

			newval=newstring
		elif(newtype=='int'):
			try:
				newval=int(newval)
			except ValueError:
				exit(32)
		elif(newtype=='bool'):
			if(newval=='true'):
				pass
			elif(newval=='false'):
				pass
			else:
				exit(32)
		elif(newtype=='nil'):
			if(newval=='nil'):
				pass
			else:
				exit(32)
		else:
			exit(32)

		#nastaveni hodnoty a typu promenne
		if(instrukce[0].attrib['type']=='var'):
			var=var_exist(instrukce[0].text)
			var['type']=newtype
			var['val']=newval
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='WRITE' and Arg_count==1):
		if(instrukce[0].attrib['type']=='var'):
			var=var_exist(instrukce[0].text)
			if(var['type']=='exist'):
				exit(56)
			elif(var['val'] is None):
				print('',end='')
			#elif(var['type']=='string'):
				#vyhledani a nahrazeni escape sequence
				#rozdeleni stringu na casti podle znaku \
				#stringpart=str(var['val']).split('\\')
				#newstring=''
				#for part in stringpart:
				#	part="\\"+part
				#	#kontrola jestli zacatek casti stringu neobsahuje escape sequenci
				#	if(part[1:4].isdigit() and len(part[1:4])==3):
				#		#nahrazeni escape sequence znakem
				#		part=part.replace(part[:4],chr(int(part[1:4])))
				#	else:
				#		part=part[1:]
				#	newstring+=part
				#vypis
				#print(newstring,end='')
			else:
				print(var['val'],end='')

		elif(instrukce[0].attrib['type']=='nil'):
			if(instrukce[0].text!='nil'):
				exit(32)

		elif(instrukce[0].attrib['type']=='string'):	
			stringpart=str(instrukce[0].text).split('\\')
			newstring=''
			for part in stringpart:
				part="\\"+part
				#vyhledani a nahrazeni escape sequence
				if(part[1:4].isdigit() and len(part[1:4])==3):
					part=part.replace(part[:4],chr(int(part[1:4])))
				else:
					part=part[1:]
				newstring+=part
			print(newstring,end='')
		else:
			print(instrukce[0].text,end='')
	elif(instrukce.attrib['opcode']=='ADD' and Arg_count==3):#var symb symb
		newval=0
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					newval=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				newval=int(instrukce[1].text)
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					newval+=int(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				newval+=int(instrukce[2].text)
			else:
				exit(53)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=newval
		else:#1. arg neni promenna
			exit(53)	
	elif(instrukce.attrib['opcode']=='SUB' and Arg_count==3):#var symb symb
		newval=0
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					newval=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				newval=int(instrukce[1].text)
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					newval-=int(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				newval-=int(instrukce[2].text)
			else:
				exit(53)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=newval
		else:#1. arg neni promenna
			exit(53)		
	elif(instrukce.attrib['opcode']=='MUL' and Arg_count==3):#var symb symb
		newval=0
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					newval=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				newval=int(instrukce[1].text)
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					newval=newval*int(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				newval=newval*int(instrukce[2].text)
			else:
				exit(53)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=newval
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='IDIV' and Arg_count==3):
		newval=0
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					newval=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int'):
				newval=int(instrukce[1].text)
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					#kontrola deleni 0
					if(var['val']==0):
						exit(57)
					newval=newval//int(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int'):
				if(instrukce[2].text==0):
					exit(57)
				newval=newval//int(instrukce[2].text)
			else:
				exit(53)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=newval
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='AND' and Arg_count==3):
		arg1=None
		arg2=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1=instrukce[1].text
			else:
				exit(53)
			#prevod hodnoty promenne do formy vhodne pro porovnani v Pythonu
			if(arg1=='true'):
				arg1=True
			elif(arg1=='false'):
				arg1=False
			else:
				exit(57)
			
			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2=instrukce[2].text
			else:
				exit(53)

			#prevod hodnoty promenne do formy vhodne pro porovnani v Pythonu
			if(arg2=='true'):
				arg2=True
			elif(arg2=='false'):
				arg2=False
			else:
				exit(57)
			#porovnani argumentu a nahrani vysledku do promenne
			var=var_exist(instrukce[0].text)
			var['type']='bool'
			if(arg1 and arg2):
				var['val']='true'
			else:
				var['val']='false'
	elif(instrukce.attrib['opcode']=='OR' and Arg_count==3):
		arg1=None
		arg2=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1=instrukce[1].text
			else:
				exit(53)

			if(arg1=='true'):
				arg1=True
			elif(arg1=='false'):
				arg1=False
			else:
				exit(57)
			
			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2=instrukce[2].text
			else:
				exit(53)

			if(arg2=='true'):
				arg2=True
			elif(arg2=='false'):
				arg2=False
			else:
				exit(57)

			var=var_exist(instrukce[0].text)
			var['type']='bool'
			if(arg1 or arg2):
				var['val']='true'
			else:
				var['val']='false'
	elif(instrukce.attrib['opcode']=='NOT' and Arg_count==2):
		arg1=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1=instrukce[1].text
			else:
				exit(53)

			if(arg1=='true'):
				arg1=True
			elif(arg1=='false'):
				arg1=False
			else:
				exit(57)

			var=var_exist(instrukce[0].text)
			var['type']='bool'
			if(not arg1):
				var['val']='true'
			else:
				var['val']='false'
	elif(instrukce.attrib['opcode']=='LT' and Arg_count==3):
		arg1=None
		arg1type=None
		arg2=None
		arg2type=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='int'):
					arg1type=var['type']
					arg1=int(var['val'])
				elif(var['type']=='string'):
					arg1type=var['type']
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1type='bool'
				arg1=instrukce[1].text
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1type='int'
				arg1=int(instrukce[1].text)
			elif(instrukce[1].attrib['type']=='string'):
				arg1type='string'
				arg1=instrukce[1].text
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='int'):
					arg2type=var['type']
					arg2=int(var['val'])
				elif(var['type']=='string'):
					arg2type=var['type']
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2type='bool'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2type='int'
				arg2=int(instrukce[2].text)
			elif(instrukce[2].attrib['type']=='string'):
				arg2type='string'
				arg2=instrukce[2].text
			else:
				exit(53)

			var=var_exist(instrukce[0].text)
			var['type']='bool'

			if(arg1type==arg2type):
				if(arg1type=='bool'):
					if(arg1=='true'):
						arg1=True
					elif(arg1=='false'):
						arg1=False
					else:
						exit(32)
					if(arg2=='true'):
						arg2=True
					elif(arg2=='false'):
						arg2=False
					else:
						exit(32)
				if(arg1<arg2):
					var['val']='true'
				else:
					var['val']='false'
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='GT' and Arg_count==3):
		arg1=None
		arg1type=None
		arg2=None
		arg2type=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='int'):
					arg1type=var['type']
					arg1=int(var['val'])
				elif(var['type']=='string'):
					arg1type=var['type']
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1type='bool'
				arg1=instrukce[1].text
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1type='int'
				arg1=int(instrukce[1].text)
			elif(instrukce[1].attrib['type']=='string'):
				arg1type='string'
				arg1=instrukce[1].text
			else:
				exit(53)

			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='int'):
					arg2type=var['type']
					arg2=int(var['val'])
				elif(var['type']=='string'):
					arg2type=var['type']
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2type='bool'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2type='int'
				arg2=int(instrukce[2].text)
			elif(instrukce[2].attrib['type']=='string'):
				arg2type='string'
				arg2=instrukce[2].text
			else:
				exit(53)

			var=var_exist(instrukce[0].text)
			var['type']='bool'
			
			if(arg1type==arg2type):
				#uprava hodnot pro porovnani
				if(arg1type=='bool'):
					if(arg1=='true'):
						arg1=True
					elif(arg1=='false'):
						arg1=False
					else:
						exit(57)
					if(arg2=='true'):
						arg2=True
					elif(arg2=='false'):
						arg2=False
					else:
						exit(57)
				#porovnani
				if(arg1>arg2):
					var['val']='true'
				else:
					var['val']='false'
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='EQ' and Arg_count==3):
		arg1=None
		arg1type=None
		arg2=None
		arg2type=None
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='int'):
					arg1type=var['type']
					arg1=int(var['val'])
				elif(var['type']=='string'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='nil'):
					arg1type=var['type']
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1type='bool'
				arg1=instrukce[1].text
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1type='int'
				arg1=int(instrukce[1].text)
			elif(instrukce[1].attrib['type']=='string'):
				arg1type='string'
				arg1=instrukce[1].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg1type='nil'
				arg1=instrukce[2].text
			else:
				exit(53)
			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='int'):
					arg2type=var['type']
					arg2=int(var['val'])
				elif(var['type']=='string'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='nil'):
					arg2type=var['type']
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2type='bool'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2type='int'
				arg2=int(instrukce[2].text)
			elif(instrukce[2].attrib['type']=='string'):
				arg2type='string'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg2type='nil'
				arg2=instrukce[2].text
			else:
				exit(53)
			#porovnani argumentu
			var=var_exist(instrukce[0].text)
			var['type']='bool'
			if(arg1type==arg2type):
				#uprava hodnot pro porovnani
				if(arg1type=='bool'):
					if(arg1=='true'):
						arg1=True
					elif(arg1=='false'):
						arg1=False
					else:
						exit(57)
					if(arg2=='true'):
						arg2=True
					elif(arg2=='false'):
						arg2=False
					else:
						exit(57)
				elif(arg1type=='nil'):
					if(arg1=='nil'):
						arg1=None
					else:
						exit(57)
					if(arg2=='nil'):
						arg2=None
					else:
						exit(57)
				#porovnani
				if(arg1==arg2):
					var['val']='true'
				else:
					var['val']='false'
			elif(arg1type=='nil' or arg2type=='nil'):
				var['val']='false'
			else:
				exit(53)
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='INT2CHAR' and Arg_count==2):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					arg1=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1=int(instrukce[1].text)
			else:
				exit(53)
			#prevod cisla na znak
			try:
				arg1=chr(arg1)
			except ValueError:
				exit(58)
			var=var_exist(instrukce[0].text)
			var['type']='string'
			var['val']=arg1
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='STRI2INT' and Arg_count==3):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='string'):
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='string'):
				arg1=instrukce[1].text
			else:
				exit(53)
			##Argument 3
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					arg2=int(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2=int(instrukce[2].text)
			else:
				exit(53)
			if(arg2>len(arg1)-1):
				exit(58)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=ord(arg1[arg2])
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='CONCAT' and Arg_count==3):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='exist'):
					exit(56)
				elif(var['type']=='string'):
					arg1=str(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='string'):
				arg1=str(instrukce[1].text)
			else:
				exit(32)
			##Argument 3
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='exist'):
					exit(56)
				elif(var['type']=='string'):
					arg2=str(var['val'])
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='string'):
				arg2=str(instrukce[2].text)
			else:
				exit(32)

			var=var_exist(instrukce[0].text)
			if(arg1=='None'):
				arg1=''
			if(arg2=='None'):
				arg2=''
			var['type']='string'
			var['val']=arg1+arg2
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='STRLEN' and Arg_count==2):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='string'):
					arg1=var['val']
				elif(var['type']=='exist'):
					exit(56)
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='string'):
				arg1=instrukce[1].text
				if(arg1 is None):
					arg1=''
				#prevod escape sequenci
				stringpart=str(arg1).split('\\')
				newstring=''
				for part in stringpart:
					part="\\"+part
					if(part[1:4].isdigit() and len(part[1:4])==3):
						part=part.replace(part[:4],chr(int(part[1:4])))
					else:
						part=part[1:]
					newstring+=part
				arg1=newstring

			else:
				exit(32)
			var=var_exist(instrukce[0].text)
			var['type']='int'
			var['val']=len(arg1)
		else:#1. arg neni promenna
			exit(32)
	elif(instrukce.attrib['opcode']=='GETCHAR' and Arg_count==3):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='string'):
					arg1=str(var['val'])
				elif(var['type']=='exist'):
					exit(56)
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='string'):
				arg1=str(instrukce[1].text)
			else:
				exit(53)
			##Argument 3
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='int'):
					arg2=int(var['val'])
				elif(var['type']=='exist'):
					exit(56)
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='int'):
				arg2=int(instrukce[2].text)
			else:
				exit(53)
			if(arg2>len(arg1)-1):
				exit(58)
			var=var_exist(instrukce[0].text)
			var['type']='string'
			var['val']=arg1[arg2]
		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='SETCHAR' and Arg_count==3):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='int'):
					arg1=int(var['val'])
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='int'):
				arg1=int(instrukce[1].text)
			else:
				exit(53)
			##Argument 3
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='string'):
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='string'):
				arg2=instrukce[2].text
			else:
				exit(53)
			if(arg2==None):
				exit(58)

			var=var_exist(instrukce[0].text)
			if(var['type']=='string'):

				newstr = list(var['val'])
				#kontrola jestli index neni mimo string
				if(arg1>len(newstr)-1):
					exit(58)
				elif(arg2==''):
					exit(58)
				else:
					newstr[arg1] = arg2[0]
					var['val'] = ''.join(newstr)
			else:
				exit(53)

		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='TYPE' and Arg_count==2):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='exist'):
					arg1=''
				else:
					arg1=var['type']				
					
			elif(instrukce[1].attrib['type']=='int'):
				arg1='int'
							
			elif(instrukce[1].attrib['type']=='bool'):
				arg1='bool'
							
			elif(instrukce[1].attrib['type']=='string'):
				arg1='string'
							
			elif(instrukce[1].attrib['type']=='nil'):
				arg1='nil'
			else:
				exit(53)
			
			var=var_exist(instrukce[0].text)
			var['type']='string'
			var['val']=arg1
		

		else:#1. arg neni promenna
			exit(53)
	elif(instrukce.attrib['opcode']=='EXIT' and Arg_count==1):
		##Argument 2
		if(instrukce[0].attrib['type']=='var'):
			var=var_exist(instrukce[0].text)
			if(var['type']=='int'):
				arg1=var['val']
			else:				
				exit(56)
		elif(instrukce[0].attrib['type']=='int'):
			arg1=instrukce[0].text
		else:
			exit(53)
		try:
			arg1=int(arg1)
		except ValueError:
			exit(57)
		if(int(arg1)>=0 and int(arg1)<=49):
			exit(int(arg1))
		else:
			exit(57)
	elif(instrukce.attrib['opcode']=='READ' and Arg_count==2):
		if(instrukce[0].attrib['type']=='var'):
			##Argument 2
			if(instrukce[1].attrib['type']=='type'):
				arg1=instrukce[1].text		
			else:
				exit(32)

			var=var_exist(instrukce[0].text)
			if(InputArg==True):
				newinput=Inputfile.readline().rstrip('\n')
			else:
				newinput=input()

			var['type']=arg1

			if(arg1=='bool'):
				if(newinput.lower()=="true"):
					newinput='true'
				else:
					newinput='false'	
			elif(arg1=='int'):
				try:
					newinput=int(newinput)
				except ValueError:
					newinput=0			
			elif(arg1=='string'):
				if(newinput==None):
					newinput=''
			else:
				exit(32)
			var['val']=newinput

		else:#1. arg neni promenna
			exit(32)
	#ramcove instrukce
	elif(instrukce.attrib['opcode']=='CREATEFRAME' and Arg_count==0):
		if(LF==None):
			LF=list(dict())
			#LF.append(dict())
		TF={}
		FrameCount=FrameCount+1
	elif(instrukce.attrib['opcode']=='PUSHFRAME' and Arg_count==0):
		ThisFrame=ThisFrame+1
		#kontrola jestli se neznazim pushnout ramec ktery neexistuje
		if ThisFrame>FrameCount:
			exit(55)
		if TF !=None:
			LF.append(TF)
			TF=None
		else:
			exit(55)
	elif(instrukce.attrib['opcode']=='POPFRAME' and Arg_count==0):
		ThisFrame=ThisFrame-1
		if ThisFrame<0:
			exit(55)
		if(LF!=None):
			TF=LF[-1]
			LF.pop()
		else:
			exit(55)
	#ladici funkce
	elif(instrukce.attrib['opcode']=='BREAK' and Arg_count==0):
		pass
	elif(instrukce.attrib['opcode']=='DPRINT' and Arg_count==1):
		pass
	elif(instrukce.attrib['opcode']=='LABEL' and Arg_count==1):
		#kod funkce pro instrukci label je ve funkci label_finder()
		pass
	elif(instrukce.attrib['opcode']=='JUMP' and Arg_count==1):
		if(instrukce[0].attrib['type']=='label'):
			if instrukce[0].text in Labels.keys():
				#nastaveni nasledujici instrukce na hodnotu ze slovniku Label
				active_instr=Labels[instrukce[0].text]
				next_instr=False
			else:
				exit(52)
		else:
			exit(53)
	elif(instrukce.attrib['opcode']=='JUMPIFEQ' and Arg_count==3):
		arg1=None
		arg1type=None
		arg2=None
		arg2type=None
		if(instrukce[0].attrib['type']=='label'):
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='int'):
					arg1type=var['type']
					arg1=int(var['val'])
				elif(var['type']=='string'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='nil'):
					arg1type=var['type']
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1type='bool'
				arg1=instrukce[1].text
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1type='int'
				arg1=int(instrukce[1].text)
			elif(instrukce[1].attrib['type']=='string'):
				arg1type='string'
				arg1=instrukce[1].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg1type='nil'
				arg1=instrukce[2].text
			else:
				exit(53)
			##Argument 3
			if(instrukce[2].attrib['type']=='var'):
				
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='int'):
					arg2type=var['type']
					arg2=int(var['val'])
				elif(var['type']=='string'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='nil'):
					arg2type=var['type']
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2type='bool'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2type='int'
				arg2=int(instrukce[2].text)
			elif(instrukce[2].attrib['type']=='string'):
				arg2type='string'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg2type='nil'
				arg2=instrukce[2].text
			else:
				exit(53)
			#porovnani
			if(arg1type==arg2type):	
				if(arg1==arg2):
					if instrukce[0].text in Labels.keys():
						#provedeni jumpu
						active_instr=Labels[instrukce[0].text]

						next_instr=False
					else:
						exit(53)
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='JUMPIFNEQ' and Arg_count==3):
		arg1=None
		arg1type=None
		arg2=None
		arg2type=None
		if(instrukce[0].attrib['type']=='label'):
			if(instrukce[1].attrib['type']=='var'):
				var=var_exist(instrukce[1].text)
				if(var['type']=='bool'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='int'):
					arg1type=var['type']
					arg1=int(var['val'])
				elif(var['type']=='string'):
					arg1type=var['type']
					arg1=var['val']
				elif(var['type']=='nil'):
					arg1type=var['type']
					arg1=var['val']
				else:
					exit(53)
			elif(instrukce[1].attrib['type']=='bool'):
				arg1type='bool'
				arg1=instrukce[1].text
			elif(instrukce[1].attrib['type']=='int' and instrukce[1].text.isdigit()):
				arg1type='int'
				arg1=int(instrukce[1].text)
			elif(instrukce[1].attrib['type']=='string'):
				arg1type='string'
				arg1=instrukce[1].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg1type='nil'
				arg1=instrukce[2].text
			else:
				exit(53)
			##Argument 3	
			if(instrukce[2].attrib['type']=='var'):
				var=var_exist(instrukce[2].text)
				if(var['type']=='bool'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='int'):
					arg2type=var['type']
					arg2=int(var['val'])
				elif(var['type']=='string'):
					arg2type=var['type']
					arg2=var['val']
				elif(var['type']=='nil'):
					arg2type=var['type']
					arg2=var['val']
				else:
					exit(53)
			elif(instrukce[2].attrib['type']=='bool'):
				arg2type='bool'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='int' and instrukce[2].text.isdigit()):
				arg2type='int'
				arg2=int(instrukce[2].text)
			elif(instrukce[2].attrib['type']=='string'):
				arg2type='string'
				arg2=instrukce[2].text
			elif(instrukce[2].attrib['type']=='nil'):
				arg2type='nil'
				arg2=instrukce[2].text
			else:
				exit(53)
			if(arg1type==arg2type):
				if(arg1!=arg2):
					if instrukce[0].text in Labels.keys():
						active_instr=Labels[instrukce[0].text]
						next_instr=False
					else:
						exit(52)
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='CALL' and Arg_count==1):
		if(instrukce[0].attrib['type']=='label'):
			#ulozeni aktualni pozice aby instrukce RETURN vedela kam se vratit
			CallStack.append(active_instr)
			if instrukce[0].text in Labels.keys():
				active_instr=Labels[instrukce[0].text]
				next_instr=False
			else:
				exit(52)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='RETURN' and Arg_count==0):
		if(len(CallStack)>0):
			active_instr=CallStack[-1]
			CallStack.pop()
		else:
			exit(56)
	#zasobnikove instrukce
	elif(instrukce.attrib['opcode']=='PUSHS' and Arg_count==1):
		if(instrukce[0].attrib['type']=='var'):
			var=var_exist(instrukce[0].text)
			if(var['type']!='exist'):
				Stack.append([var['type'],var['val']])
			else:
				exit(56)
		elif(instrukce[0].attrib['type']=='int'):
			Stack.append([instrukce[0].attrib['type'],instrukce[0].text])
		elif(instrukce[0].attrib['type']=='string'):
			Stack.append([instrukce[0].attrib['type'],instrukce[0].text])
		elif(instrukce[0].attrib['type']=='bool'):
			Stack.append([instrukce[0].attrib['type'],instrukce[0].text])
		elif(instrukce[0].attrib['type']=='nil'):
			Stack.append([instrukce[0].attrib['type'],instrukce[0].text])
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='POPS' and Arg_count==1):
		if(instrukce[0].attrib['type']=='var'):
			var=var_exist(instrukce[0].text)
			if(len(Stack)>0):
				var['type']=Stack[-1][0]
				var['val']=Stack[-1][1]
				Stack.pop()
			else:
				exit(56)
		else:
			exit(32)
	#instrukce rozsireni STACK
	elif(instrukce.attrib['opcode']=='CLEARS' and Arg_count==0):
		Stack=list()
	elif(instrukce.attrib['opcode']=='ADDS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(arg1type=='int' and arg2type=='int'):
				Stack.append(['int',str(int(arg1val)+int(arg2val))])
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='SUBS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(arg1type=='int' and arg2type=='int'):
				Stack.append(['int',str(int(arg1val)-int(arg2val))])
			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='MULS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(arg1type=='int' and arg2type=='int'):
				Stack.append(['int',str(int(arg1val)*int(arg2val))])
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='IDIVS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(arg1type=='int' and arg2type=='int'):
				if(int(arg2val)!=0):
					Stack.append(['int',str(int(arg1val)//int(arg2val))])
				else:
					exit(57)
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='LTS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]

			if(arg1type==arg2type):

				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				elif(arg1type=='int'):
					arg1val=int(arg1val)
					arg2val=int(arg2val)
				if(arg1val<arg2val):
					Stack.append(['bool','true'])
				else:
					Stack.append(['bool','false'])
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='GTS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]

			if(arg1type==arg2type):

				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				elif(arg1type=='int'):
					arg1val=int(arg1val)
					arg2val=int(arg2val)
				if(arg1val>arg2val):
					Stack.append(['bool','true'])
				else:
					Stack.append(['bool','false'])
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='EQS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]

			if(arg1type=='bool'):
				if(arg1val=='true'):
					arg1val=True
				elif(arg1val=='false'):
					arg1val=False
				else:
					exit(32)
			elif(arg1type=='nil'):
				if(arg1val=='nil'):
					arg1val=None
				else:
					exit(57)
			elif(arg1type=='int'):
				arg1val=int(arg1val)
			
			if(arg2type=='bool'):
				if(arg2val=='true'):
					arg2val=True
				elif(arg2val=='false'):
					arg2val=False
				else:
					exit(32)
			elif(arg2type=='nil'):
				if(arg2val=='nil'):
					arg2val=None
				else:
					exit(57)
			elif(arg2type=='int'):
				arg2val=int(arg2val)
			
			if(arg1type==arg2type):
				if(arg1val==arg2val):
					Stack.append(['bool','true'])
				else:
					Stack.append(['bool','false'])
			elif(arg1type=='nil' or arg2type=='nil'):
				Stack.append(['bool','false'])
			else:
				exit(53)

		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='ANDS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]

			if(arg1type==arg2type):
				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				else:
					exit(53)

				if(arg1val and arg2val):
					Stack.append(['bool','true'])
				else:
					Stack.append(['bool','false'])
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='ORS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]

			if(arg1type==arg2type):
				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				else:
					exit(53)

				if(arg1val or arg2val):
					Stack.append(['bool','true'])
				else:
					Stack.append(['bool','false'])
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='NOTS' and Arg_count==0):
		if(len(Stack)>=1):
			arg2type=Stack[-1][0]
			arg2val=Stack[-1][1]
			if(arg2type=='bool'):
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
			else:
				exit(53)
			if(not arg2val):
				Stack.append(['bool','true'])
			else:
				Stack.append(['bool','false'])
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='INT2CHARS' and Arg_count==0):
		if(len(Stack)>=1):
			arg2type=Stack[-1][0]
			arg2val=Stack[-1][1]
			if(arg2type=='int'):					
				try:
					Stack.append(['string',chr(int(arg2val))])
				except ValueError:
					exit(58)
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='STRI2INTS' and Arg_count==0):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg2val=Stack[-1][1]
			arg1type=Stack[-2][0]
			arg1val=Stack[-2][1]
			if(arg2type=='int' and arg1type=='string'):
				try:
					Stack.append(['string',ord(arg1val[int(arg2val)])])
				except IndexError:
					exit(58)	
			else:
				exit(53)
		else:
			exit(32)
	elif(instrukce.attrib['opcode']=='JUMPIFEQS' and Arg_count==1):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(instrukce[0].attrib['type']!='label'):
				exit(32)
			if(arg1type==arg2type):
				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				elif(arg1type=='nil'):
					if(arg1val=='nil'):
						arg1val=None
					else:
						exit(57)
					if(arg2val=='nil'):
						arg2val=None
					else:
						exit(57)
				elif(arg1type=='int'):
					arg1val=int(arg1val)
					arg2val=int(arg2val)

				if(arg1val==arg2val):
					active_instr=Labels[instrukce[0].text]
					next_instr=False

			else:
				exit(53)
	elif(instrukce.attrib['opcode']=='JUMPIFNEQS' and Arg_count==1):
		if(len(Stack)>=2):
			arg2type=Stack[-1][0]
			arg1type=Stack[-2][0]
			arg2val=Stack[-1][1]
			arg1val=Stack[-2][1]
			if(instrukce[0].attrib['type']!='label'):
				exit(32)
			if(arg1type==arg2type):
				if(arg1type=='bool'):
					if(arg1val=='true'):
						arg1val=True
					elif(arg1val=='false'):
						arg1val=False
					else:
						exit(32)
					if(arg2val=='true'):
						arg2val=True
					elif(arg2val=='false'):
						arg2val=False
					else:
						exit(32)
				elif(arg1type=='nil'):
					if(arg1val=='nil'):
						arg1val=None
					else:
						exit(57)
					if(arg2val=='nil'):
						arg2val=None
					else:
						exit(57)
				elif(arg1type=='int'):
					arg1val=int(arg1val)
					arg2val=int(arg2val)

				if(arg1val!=arg2val):
					active_instr=Labels[instrukce[0].text]
					next_instr=False

			else:
				exit(53)
		else:
			exit(32)
	else:
		exit(32)
	#nastaveni dalsi instrukce v poradi
	if(next_instr==True):
		active_instr=active_instr+1
	else:
		next_instr=True

#vypis pro rozsireni STATI
if(StatsArg):
	for arg in StatsArgs_List:
		print
		if(arg==1):
			Statsfile.write(str(stat_instrCount)+"\n")
		else:
			Statsfile.write(str(stat_varcount)+"\n")
	Statsfile.close()
#zavirani pouzitych souboru
if(InputArg):
	Inputfile.close()

file.close()