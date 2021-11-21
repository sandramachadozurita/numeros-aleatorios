
'''
Created on 28/10/2021

@author: Outros
'''
    
from flask import Flask, render_template, redirect, request, url_for, session, flash
from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup
from beebotte import *

import bcrypt
import requests
import re
import time
import threading


app = Flask(__name__)  

app.secret_key = "ayush"


_accesskey  = 'NhcLj3pytanhH0Gizy4c927Z'
_secretkey  = '8DfMkZc2PqLHUebLEd2TAFjf9Zq65IEG'
_hostname   = 'api.beebotte.com'
bbt = BBT( _accesskey, _secretkey, hostname = _hostname)

### Alternatively you can authenticate using the channel token
# _token      = 'token_lnGng7n1SZ60ilv8'
# bbt = BBT(token = _token, hostname = _hostname)


# Method to store data in elasticsearch
def send_data_to_es(_id, data):
 es=Elasticsearch(['localhost:9200'])
 res = es.index(index='numeros',doc_type='n', id=_id, body=data)
 
def send_data(data):
    es=Elasticsearch(['localhost:9200'])
    x=es.index(index='usuarios',  body=data)      

def send_promedio(data):
   es=Elasticsearch(['localhost:9200'])
   promedio=es.index(index='promedios', doc_type='n', body=data)

   
   
 # Method to get data from elasticsearch
def get_last_number():
 es=Elasticsearch(['localhost:9200'])
 x = es.search(index='numeros', body={"query":{"match_all":{}}})
 n_size = x["hits"]["total"]["value"]-1
 return x["hits"]["hits"][n_size]["_source"]['numero']

  
 #Method to get media from elasticsearch
def get_media():
 es=Elasticsearch(['localhost:9200'])
 media=es.search(index='numeros', doc_type='n', body={"query":{"match_all":{}}, "size": 0, "aggs": {"quantity_avg": {"avg":{"field":"numero"}}}})
 send_promedio(data = {"promedio": media ["aggregations"]["quantity_avg"]["value"]})
 return media ["aggregations"]["quantity_avg"]["value"]
 
def get_media_Internet(): 
 es=Elasticsearch(['localhost:9200'])
 # x = es.search(index='numeros', body={"query": {"match": {'_id':'0'}}})
 x = es.search(index='numeros', body={"query":{"match_all":{}}})
 n_size = x["hits"]["total"]["value"]
 ax = bbt.read("numeros_aleatorios", "numeros", limit = n_size)
 numeros = []
 for i in range(n_size):
     numeros.append(ax[i]["data"])
 return sum(numeros)/len(numeros)


def deleteIndex(_index):
    es=Elasticsearch(['localhost:9200'])
    res = es.indices.delete(index=_index, ignore=[400, 404])
    return res


def ejecucion_horaria(segundos):
    """
    Este es un thread con parametros.

    @param segundos: Ejecuta un print cada tantos segundos. 

    """

    print("Esto se ejecutara cada %d" % segundos )

    id = 0 
    while True:
        result = requests.get("https://www.numeroalazar.com.ar/")
        contenido = result.content
        soup = BeautifulSoup(contenido, 'lxml')


        for div in soup.find_all("div"):
            if(div.attrs['id'] == 'numeros_generados'):
                x = re.findall('[0-9]{2}\.[0-9]{2}', div.text)
                y = float (x[0])
                print(y)
                bbt.write("numeros_aleatorios", "numeros", y)
                send_data_to_es(id, data = {"numero": y})
                id += 1
                break   
        time.sleep(segundos)
            




#--------------------------------------------------------------------------------------#
deleteIndex("numeros")
deleteIndex("usuarios")
hilo = threading.Thread(target=ejecucion_horaria, args=(120,))
hilo.start()   # Iniciamos la ejecuci�n del thread,




@app.route('/')
def main():
    return render_template("index.html") 

@app.route('/register')
def register():   
    return render_template("register.html") 


@app.route('/register/numero', methods=["POST"])  
def Numeros_aleatorios(): 
    if request.method == "POST":  
        session['nombre']=request.form['nombre'] 

    if 'nombre' in session: 
        passwd = request.form['pass']
        encode_pass = passwd.encode()
        clave_cifrada = bcrypt.hashpw(encode_pass, bcrypt.gensalt())
        nombre = session['nombre'] 
        correo = request.form['correo']
        send_data(data = {"usuario": nombre, "correo": correo, "password": clave_cifrada.decode() })
        return render_template("numero.html", numero=get_last_number(), nomb=nombre, value = get_media())    
    else:  
        return '<p>Por favor registrate primero</p>'


@app.route('/promedio', methods=["GET"])
def promedio():  
        nombre = session['nombre'] 
        promedio = get_media() 
        return render_template("numero.html", prom=promedio, nomb=nombre, numero=get_last_number())
    
@app.route('/promedio-internet', methods=["GET"])
def promedioInternet():  
        nombre = session['nombre'] 
        promedio = get_media_Internet() 
        return render_template("numero.html", promedioInternet=promedio, nomb=nombre, numero=get_last_number())


@app.route('/logout')  
def logout(): 
  if 'nombre' in session:  
    session.pop('nombre',None)  
    return render_template('index.html');  
  else:  
    return '<p>el usuario ha cerrado su sesion</p>'  



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    
    


