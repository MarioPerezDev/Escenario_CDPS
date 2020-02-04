#!/usr/bin/env python3
import sys
import os
from lxml import etree
import configparser
import subprocess
import time

#Variables globales que se utilizaran durante toda la practica
ordenes = ["crear", "arrancar", "parar", "destruir", "help", "prueba","check", "monitor", "haproxy"]
maquinas = ["lb","c1","s1","s2", "s3", "s4", "s5"]
multiples = ["crear", "arrancar", "parar","monitor"]
ips = ["","10.0.1.2","10.0.2.11","10.0.2.12","10.0.2.13","10.0.2.14","10.0.2.15"]
config = configparser.ConfigParser()

def help():
	print("AYUDA:")
	print("Para utilizar el script, escriba \"sudo ./pf1.py <comando> <opción>\"")
	print("Los comandos disponibles son: crear, arrancar, parar, destruir, check, monitor, haproxy y help\n")
	print("Escriba \"sudo ./pf1.py crear <Numero>\" para crear las MV referentes a los servidores.")
	print("	-Siendo <Numero> el número de servidores a crear")
	print("	-El <Número> debe estar comprendido entre 1 y 5.")
	print("	-Si no se introduce valor, se crearán 2 servidores.\n")
	print("Escriba \"sudo ./pf1.py arrancar <opción>\" para arrancar las MV.")
	print("	-La opción sirve para elegir qué máquina arrancar en caso de que sólo quiera arrancarse una.")
	print("	-No introducir opción (escribiendo solo \"sudo ./pf1.py arrancar\") arrancará todas las máquinas.")
	print("	-Las opciones posibles son lb, c1, s1, s2, s3, s4, s5 (en función de cuantos servidores se hayan creado anteriormente.)")
	print("		Por ejemplo, escribir \"sudo ./pf1.py arrancar s1\" arrancará solo el servidor s1.\n")
	print("Escriba \"sudo ./pf1.py parar <opción>\" para parar las MV.\n")
	print("	-La opción sirve para elegir qué máquina parar en caso de que sólo quiera pararse una.")
	print("	-No introducir opción (escribiendo solo \"sudo ./pf1.py parar\") parará todas las máquinas.")
	print("	-Las opciones posibles son lb, c1, s1, s2, s3, s4, s5 (en función de cuantos servidores se hayan arrancado anteriormente.)")
	print("		Por ejemplo, escribir \"sudo ./pf1.py arrancar s1\" arrancará solo el servidor s1.\n")
	print("Escriba \"sudo ./pf1.py destruir\" para eliminar todos los archivos que hayan sido creados.\n")
	print("Escriba \"sudo ./pf1.py check\" para comprobar las conexiones del host con el resto de máquinas.\n")
	print("Escriba \"sudo ./pf1.py monitor <opción> <opción2>\" para monitorizar aspectos del entorno.")
	print("	-Las opciones principales de monitor son: -state -cpus -info")
	print("	-Escribir sólo la primera opción monitorizará todas las máquinas.")
	print("		Por ejemplo, escribir \"sudo ./pf1.py monitor -info\" dará la información de todas las máquinas")
	print("	-Escribir el nombre de una máquina en la segunda opción permite monitorizarla.")
	print("		Por ejemplo, escribir \"sudo ./pf1.py monitor -cpus s1\" dará la información de los cpus sólo de s1\n")
	print("Escriba \"sudo ./pf1.py haproxy\" para comprobar que el haproxy funciona correctamente.")







def check():
	for maquina in maquinas:
		if os.path.isfile('./'+maquina+'.qcow2'):
			print("El fichero qcow2 de "+maquina+" ha sido creado correctamente.")
		if os.path.isfile('./'+maquina+'.xml'):
			print("El fichero xml de "+maquina+" ha sido creado correctamente.")



def crear(num):
#Esto simplemente crea el fichero de configuracion pf1.cfg que lleva dentro el numero de servidores arrancados
#Usamos el modulo configparser por lo tanto se guarda el numero pasado por el comando crear en num_serv de pf1.cfg
	if not os.path.exists('./pf1.cfg'):
		os.mknod('./pf1.cfg')
		config.read('pf1.cfg')
		config.add_section('main')
		for index in range (0, num + 2):
			config.set('main',maquinas[index],maquinas[index])
		config.set('main','num_serv', str(num))
		with open('pf1.cfg', 'w') as f:
			config.write(f)
	else:
		config.read('pf1.cfg')
		for index in range (0, num + 2):
			config.set('main',maquinas[index],maquinas[index])
		config.set('main','num_serv', str(num))
		with open('pf1.cfg', 'w') as f:
			config.write(f)

#Creacion de MVs de los Servidores. Como numero es el introducido con el comando, se crearán ese número de Servidores
#siendo de forma predeterminada 2
	for index in range(num+2):
		server=maquinas[index]
		os.system('qemu-img create -f qcow2 -b cdps-vm-base-pf1.qcow2 '+server+'.qcow2')
		os.system('cp plantilla-vm-pf1.xml '+server+'.xml')

		# Cargamos el fichero xml
		tree = etree.parse(server+'.xml')
		# Obtenemos el nodo raiz e imprimimos su nombre y el valor del atributo 'tipo'
		root = tree.getroot()
		# Buscamos la etiqueta 'nombre' imprimimos su valor y luego lo cambiamos
		name = root.find("name")
		name.text = server

		# Buscamos la etiqueta 'nombre' bajo el nodo 'parte3' e imprimimos su valor y luego lo cambiamos
		sourcefile=root.find("./devices/disk/source[@file='/mnt/tmp/XXX/XXX.qcow2']")
		sourcefile.set("file", "/home/jepeme/Documentos/CDPS/pf1/" +server+".qcow2")

		#Esto solo será necesario en lb (añadir el segundo bridge)
		if server == "lb":
			sourceInterface2 = root.find("./devices")
			interface2 = etree.SubElement(sourceInterface2, "interface", type='bridge')
			source2 = etree.SubElement(interface2, "source", bridge='LAN2')
			model2 = etree.SubElement(interface2, "model", type='virtio')

		#Ahora en función de qué sea tendrá de configuración LAN1 (c1 y lb) o LAN2 (s1-s5)
		sourcebridge=root.find("./devices/interface/source[@bridge='XXX']")
		if server == "lb" or server == "c1":
			sourcebridge.set("bridge", "LAN1")
		else:
			sourcebridge.set("bridge", "LAN2")

		#Se modifican los ficheros xml de cada una de las máquinas
		out=open(server+".xml", "w")
		out.write(etree.tostring(tree, encoding="unicode"))
		out.close()

	#Creacion de los bridges correspondientes a las dos redes virtuales
	os.system("sudo brctl addbr LAN1")
	os.system("sudo brctl addbr LAN2")
	os.system("sudo ifconfig LAN1 up")
	os.system("sudo ifconfig LAN2 up")

	os.system("sudo ifconfig LAN1 10.0.1.3/24")
	os.system("sudo ip route add 10.0.0.0/16 via 10.0.1.1")
	config.read('pf1.cfg')
	numservers= int(config.get('main', 'num_serv'))
	print ("El número de servidores a arrancar es: " +str(numservers))
	print("Configurando interfaces, por favor, espere...")
	os.system("sudo virt-copy-out -a s1.qcow2 /etc/network/interfaces . ; mv interfaces plantillainterfaces")

	for index in range(0,numservers+2):
		maquina = maquinas[index]
		print("Cambiando valores de "+maquina+", por favor, espere...")
		file = open('hostname', 'w+')
		file.write(maquina)
		file.close()
		os.system("sudo virt-copy-in -a "+maquina+".qcow2 hostname /etc")
		file = open('hosts', 'w+')
		file.writelines(["127.0.1.1 "+maquina+" "+maquina,
		"\n127.0.0.1 localhost",
		"\n::1 ip6-localhost ip6-loopback" ,
		"\nfe00::0 ip6-localnet" ,
		"\nff00::0 ip6-mcastprefix",
		"\nff02::1 ip6-allnodes",
		"\nff02::2 ip6-allrouters",
		"\nff02::3 ip6-allhosts"])
		file.close()
		print ("Definiendo "+maquina)
		# Lanzamos s1
		os.system('sudo virsh define ' +maquina+'.xml')
		os.system("sudo virt-copy-in -a "+maquina+".qcow2 hosts /etc")

		if(maquina) == "lb":
			aux = open("plantillainterfaces", "r")
			interfaces = open("interfaces", "w+")
			for line in aux:
				if "iface lo inet loopback" in line:
					interfaces.writelines([line,
					 "\nauto eth1" ,
					 "\niface eth1 inet static",
					 "\naddress 10.0.2.1",
					 "\nnetmask 255.255.255.0",
					 "\nnetwork 10.0.2.0",
					 "\nbroadcast 10.0.2.255",
					 "\nauto eth0",
					 "\niface eth0 inet static",
					 "\naddress 10.0.1.1",
					 "\nnetmask 255.255.255.0",
					 "\nnetwork 10.0.1.0",
					 "\nbroadcast 10.0.1.255\n"])
				else:
					interfaces.write(line)
			interfaces.close()
			aux.close()
			os.system("sudo virt-copy-in -a "+maquina+".qcow2 interfaces /etc/network")

			#Para que el balanceador de tráfico funcione como router al arrancar, modificamos el fichero
			#/etc/sysctl.conf
			print("Configurando correctamente el balanceador de tráfico...")
			os.system("sudo virt-copy-out -a lb.qcow2 /etc/sysctl.conf . ; mv sysctl.conf plantillasysctl.conf")
			aux = open("plantillasysctl.conf", "r")
			sysctl = open("sysctl.conf", "w+")
			for line in aux:
				if "#net.ipv4.ip_forward=1" in line:
					sysctl.write("net.ipv4.ip_forward=1\n")
				else:
					sysctl.write(line)
			sysctl.close()
			aux.close()
			os.system("sudo virt-copy-in -a lb.qcow2 sysctl.conf /etc")
			os.system('rm -f plantillasysctl.conf')
			os.system('rm -f sysctl.conf')

			print(maquina + " :Configurando correctamente el balanceador de tráfico...")
			os.system("sudo virt-copy-out -a lb.qcow2 /etc/haproxy/haproxy.cfg .")
			with open("haproxy.cfg", "a") as file:
			    file.writelines(["frontend lb\n",
							"bind *:80\n",
							"mode http\n",
							"default_backend webservers\n",
							"backend webservers\n",
							"mode http\n",
							"balance roundrobin\n",
							"server s1 10.0.2.11:80 check\n",
							"server s2 10.0.2.12:80 check\n",
							"server s3 10.0.2.13:80 check\n",
							"server s2 10.0.2.14:80 check\n",
							"server s2 10.0.2.15:80 check\n"])
			os.system("sudo virt-copy-in -a lb.qcow2 haproxy.cfg /etc/haproxy")
			os.system('rm -f haproxy.cfg')

		elif(maquina) == "c1":
			aux = open("plantillainterfaces", "r")
			interfaces = open("interfaces", "w+")
			for line in aux:
				if "iface lo inet loopback" in line:
					interfaces.writelines([line,
					 "\nauto eth0" ,
					 "\niface eth0 inet static",
					 "\naddress 10.0.1.2",
					 "\nnetmask 255.255.255.0",
					 "\nnetwork 10.0.1.0",
					 "\nbroadcast 10.0.1.255",
					 "\ngateway 10.0.1.1\n"])
				else:
					interfaces.write(line)
			interfaces.close()
			aux.close()
			os.system("sudo virt-copy-in -a "+maquina+".qcow2 interfaces /etc/network")

		else:
			aux = open("plantillainterfaces", "r")
			interfaces = open("interfaces", "w+")
			for line in aux:
				if "iface lo inet loopback" in line:
					interfaces.writelines([line,
					 "\nauto eth0" ,
					 "\niface eth0 inet static",
					 "\naddress 10.0.2.1"+ str(index-1),
					 "\nnetmask 255.255.255.0",
					 "\nnetwork 10.0.2.0",
					 "\nbroadcast 10.0.1.255",
					 "\ngateway 10.0.2.1\n"])
				else:
					interfaces.write(line)
			interfaces.close()
			aux.close()

			htmlfile = open("index.html", "w+")
			htmlfile.write(maquina)
			htmlfile.close()
			os.system("sudo virt-copy-in -a "+maquina+".qcow2 interfaces /etc/network")
			os.system("sudo virt-copy-in -a "+maquina+".qcow2 index.html /var/www/html")

	check()


def parar():
	if not os.path.exists('./pf1.cfg'):
		print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
		print("A continuación verá el comando de ayuda:")
		help()
	else:
		config.read('pf1.cfg')
		numservers= int(config.get('main', 'num_serv'))

		os.system("HOME=/Documentos/CDPS/pf1 sudo virt-manager")
		if data == "all":
			print("Paramos todas")
			for server in range(0,numservers+2):
				os.system("sudo virsh shutdown "+ maquinas[server])
		else:
			# Paramos la maquina pedida
			print ("Deteniendo "+ data)
			os.system('sudo virsh shutdown ' +data)

def destruir():
	if not os.path.exists('./pf1.cfg'):
		print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
		print("A continuación verá el comando de ayuda:")
		help()
	else:
		config.read('pf1.cfg')
		numservers= int(config.get('main', 'num_serv'))
		print ("El número de servidores a destruir es: " +str(numservers))
		os.system("sudo ifconfig LAN1 down")
		os.system("sudo ifconfig LAN2 down")
		os.system("sudo brctl delbr LAN1")
		os.system("sudo brctl delbr LAN2")

		for server in maquinas:
			if os.path.isfile('./'+server+'.qcow2'):
				os.system('rm -f '+server+'.qcow2')
			if os.path.isfile('./'+server+'.xml'):
				os.system('rm -f '+server+'.xml')


		for server in range(0,numservers+2):
			os.system("sudo virsh shutdown "+ maquinas[server])
			os.system("sudo virsh destroy "+maquinas[server])
			os.system("sudo virsh undefine "+maquinas[server])

		if os.path.exists('hosts'):
			os.system("rm -f hosts")
		if os.path.exists('hostname'):
			os.system("rm -f hostname")
		if os.path.exists('index.html'):
			os.system('rm -f index.html')
		if os.path.exists("pf1.cfg"):
			os.system("rm -f pf1.cfg")
		if os.path.exists("plantillainterfaces"):
			os.system("rm -f plantillainterfaces")
		if os.path.exists("interfaces"):
			os.system("rm -f interfaces")



	print("El proyecto ha sido destruido por Jorge y Mario!! ;)")


def arrancar():
	if not os.path.exists('./pf1.cfg'):
		print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
		print("A continuación verá el comando de ayuda:")
		help()
	else:
		config.read('pf1.cfg')
		numservers= int(config.get('main', 'num_serv'))

		os.system("HOME=/Documentos/CDPS/pf1 sudo virt-manager")
		if data == "all":
			print("Arrancamos todas")
			for index in range(0, numservers+2):
				maquina = maquinas[index]
				print ("Arrancando "+maquina+ "...")
				os.system('sudo virsh start ' +maquina)
				os.system("xterm -rv -sb -rightbar -fa  monospace -fs  10  -title '"+maquina+"' -e  'sudo virsh console "+maquina+"' &")
		else:
			# Lanzamos la elegida
			print ("Arrancando "+data+ "...")
			os.system('sudo virsh start ' +data)
			os.system("xterm -rv -sb -rightbar -fa  monospace -fs  10  -title '"+data+"' -e  'sudo virsh console "+data+"' &")

def haproxy():
	print("Probando que el haproxy funciona correctamente:")
	t_end = time.time() + 8
	while time.time() < t_end:
		os.system("curl 10.0.1.1")
		time.sleep(0.4)
		print("")

#Comprueba si hay conexión al resto de máquinas desde el host
def checkConnections():
	if not os.path.exists('./pf1.cfg'):
		print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
		print("A continuación verá el comando de ayuda:")
		help()
	else:
		config.read('pf1.cfg')
		numservers= int(config.get('main', 'num_serv'))
	for index in range (1,numservers+2):
		print("Comprobando conexión con " + maquinas[index])
		os.system("ping " + ips[index] + " -c 4")
		print("\n")
	for index in range (1,numservers+1):
		print("Comprobando conexión con el html de " + maquinas[index+1])
		os.system("curl 10.0.2.1" + str(index))
		print("\n")

def monitor():
	config.read('pf1.cfg')
	numservers= int(config.get('main', 'num_serv'))
	if data == "-state":
		if len(sys.argv) == 3:
			print("Mostrando la info de las cpus de todas las máquinas.")
			for maquina in upList:
				print("Información sobre la máquina " + maquina)
				os.system("sudo virsh domstate " + maquina)
		elif len(sys.argv) == 4:
			if sys.argv[3] in upList:
				print("Información sobre la máquina " + sys.argv[3])
				os.system("sudo virsh domstate " + sys.argv[3])
			else:
				print("Dicha máquina no existe")
		else:
			print("Dicho comando no existe")
			time.sleep(1)
			help()
	elif data == "-cpus":
		if len(sys.argv) == 3:
			for maquina in upList:
				os.system("clear")
				print("Mostrando la info de las cpus de todas las máquinas.")
				print("Información sobre la máquina " + maquina)
				os.system("sudo virsh cpu-stats " + maquina)
				time.sleep(2)
		elif len(sys.argv) == 4:
			if sys.argv[3] in upList:
				print("Mostrando la info de " + sys.argv[3])
				print("Información sobre la máquina " + sys.argv[3])
				os.system("sudo virsh cpu-stats " + sys.argv[3])
			else:
				print("Dicha máquina no existe")
		else:
			print("Dicho comando no existe")
			time.sleep(1)
			help()
	elif data == "-info":
		if len(sys.argv) == 3:
			for maquina in upList:
				os.system("clear")
				print("Mostrando la info de las cpus de todas las máquinas.")
				print("Información sobre la máquina " + maquina)
				os.system("sudo virsh dominfo " + maquina)
				time.sleep(2)
		elif len(sys.argv) == 4:
			if sys.argv[3] in upList:
				print("Mostrando la info de " + sys.argv[3])
				print("Información sobre la máquina " + sys.argv[3])
				os.system("sudo virsh dominfo " + sys.argv[3])
			else:
				print("Dicha máquina no existe")
		else:
			print("Dicho comando no existe")
			time.sleep(1)
			help()
	else:
		print("Comando no disponible")
		time.sleep(2)
		help()


def ejecutarOrden(orden):
    if orden in ordenes:
        if orden == "crear":
            crear(numero)
        if orden == "arrancar":
            arrancar()
        if orden == "parar":
            parar()
        if orden == "destruir":
            destruir()
        if orden == "haproxy":
            haproxy()
        if orden == "check":
            checkConnections()
        if orden == "help":
            help()
        if orden == "monitor":
            monitor()
    else:
        print("La orden " + orden + " NO existe")

try:
	orden = sys.argv[1]
	if sys.argv[1] in multiples:
		if sys.argv[1] == "crear":
			if len(sys.argv) == 3:
				if int(sys.argv[2]) < 6 and int(sys.argv[2]) > 0:
					numero = int(sys.argv[2])
					ejecutarOrden(orden)
				else:
					print("El número elegido es incorrecto, escoja otro distinto")
			else:
				numero = 2
				ejecutarOrden(orden)

		if sys.argv[1] == "monitor":
			if not os.path.exists('./pf1.cfg'):
				print("No existe el archivo pf1.cfg, ¿Has creado y arrancado ya las Máquinas Virtuales necesarias?")
				print("A continuación verá el comando de ayuda:")
				help()
			else:
				try:
					config.read('pf1.cfg')
					maquinascreadas= int(config.get('main',"num_serv"))
					upList = []
					for index in range (0,maquinascreadas+2):
						upList.append(maquinas[index])
					if len(sys.argv) > 2:
						if sys.argv[2] == "-state":
							data = "-state"
							ejecutarOrden(orden)
						elif sys.argv[2] == "-cpus":
							data = "-cpus"
							ejecutarOrden(orden)
						elif sys.argv[2] == "-info":
							data = "-info"
							ejecutarOrden(orden)
						else:
							print("Dicha opción no existe, pruebe con otra.")
							print("A continuación verá el comando de ayuda.")
							time.sleep(2)
							help()
					else:
						print("Debes seleccionar una opción para monitorizar")
						time.sleep(2)
						help()
				except:
					print("Error, posiblemente no haya arrancado aún el sistema.")
					print("A continuación verá el comando de ayuda.")
					time.sleep(2)
					help()

		if sys.argv[1] == "arrancar":
			if not os.path.exists('./pf1.cfg'):
				print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
				print("A continuación verá el comando de ayuda:")
				help()
			else:
				try:
					config.read('pf1.cfg')
					maquinascreadas= int(config.get('main',"num_serv"))
					upList = []
					for index in range (0,maquinascreadas+2):
						upList.append(maquinas[index])
					if len(sys.argv) > 2:
						if sys.argv[2] in upList:
							print("Arrancando máquina " + sys.argv[2])
							data = sys.argv[2]
							ejecutarOrden(orden)
						elif sys.argv[2] in maquinas:
							print("La máquina " + sys.argv[2] + " no ha sido creada, no puede arrancarse.")
							print("Solo han sido creadas las máquinas: ")
							print(upList)
						else:
							print("Dicha opción no existe, pruebe con otra.")
							print("A continuación verá el comando de ayuda.")
							time.sleep(2)
							help()
					else:
						data = "all"
						ejecutarOrden(orden)
				except:
					print("Error, posiblemente no haya creado aún el sistema.")
					print("A continuación verá el comando de ayuda.")
					time.sleep(2)
					help()

		if sys.argv[1] == "parar":
			if not os.path.exists('./pf1.cfg'):
				print("No existe el archivo pf1.cfg, ¿Has creado ya las Máquinas Virtuales necesarias?")
				print("A continuación verá el comando de ayuda:")
				help()
			else:
				try:
					config.read('pf1.cfg')
					maquinascreadas= int(config.get('main',"num_serv"))
					upList = []
					for index in range (0,maquinascreadas+2):
						upList.append(maquinas[index])
					if len(sys.argv) > 2:
						if sys.argv[2] in upList:
							print("Parando máquina " + sys.argv[2])
							data = sys.argv[2]
							try:
								ejecutarOrden(orden)
							except:
								print("Esa máquina no está arrancada")
						elif sys.argv[2] in maquinas:
							print("La máquina " + sys.argv[2] + " no ha sido arrancada, no puede arrancarse.")
							print("Solo han sido creadas las máquinas: ")
							print(upList)
						else:
							print("Dicha opción no existe, pruebe con otra.")
							print("A continuación verá el comando de ayuda.")
							time.sleep(2)
							help()
					else:
						data = "all"
						ejecutarOrden(orden)
				except:
					print("Error, posiblemente no haya creado aún el sistema.")
					print("A continuación verá el comando de ayuda.")
					time.sleep(2)
					help()
	else:
		if  len(sys.argv) == 3 and sys.argv[2] not in multiples:
			print("Solo se permite un tercer argumento para crear las MV o para monitorizar el entorno con la orden monitor.")
		else:
			ejecutarOrden(orden)
except:
	help()
