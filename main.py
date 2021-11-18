
'''
Created on 28/10/2021

@author: Outros
'''
    
from flask import Flask, render_template, redirect, request, url_for, session, flash
from elasticsearch import Elasticsearch
from email._header_value_parser import get_name_addr
from bs4 import BeautifulSoup
from beebotte import *

import bcrypt
import requests
import re
import time
import threading

app = Flask(__name__)  


app.secret_key = "ayush"
bclient = BBT("API_BD", "SECRET_BD")

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
 x = es.search(index='numeros', body={"query": {"match": {'_id':'0'}}})
 return x["hits"]["hits"][0]["_source"]['numero']

  
 #Method to get media from elasticsearch
def get_media():
 es=Elasticsearch(['localhost:9200'])
 media=es.search(index='numeros', doc_type='n', body={"query":{"match_all":{}}, "size": 0, "aggs": {"quantity_avg": {"avg":{"field":"numero"}}}})
 send_promedio(data = {"promedio": media ["aggregations"]["quantity_avg"]["value"]})
 return media ["aggregations"]["quantity_avg"]["value"]


def get_data(data):
 es=Elasticsearch(['localhost:9200'])   
 name1=es.search(index='usuarios', body=data) 
 return name1

 

def existsIndex(_index):
    es=Elasticsearch(['localhost:9200'])
    res = es.indices.exists(index=_index)
    return res


def deleteIndex(_index):
    es=Elasticsearch(['localhost:9200'])
    res = es.indices.delete(index=_index, ignore=[400, 404])
    return res

# delet all item
def delete_one(_index, _id):
    es=Elasticsearch(['localhost:9200'])
    res = es.delete(index=_index, id=_id)
    return res



def ejecucion_horaria(segundos):
    """
    Este es un thread con parametros.
    
    @param segundos: Ejecuta un print cada tantos segundos. 
    
    """
    
    print("Esto se ejecutara cada %d" % segundos )
    
    
    # for i in range(20):

    i = 1
    id = 0 
    while i <= 10:
        result = requests.get("https://www.numeroalazar.com.ar/")
        contenido = result.content
        soup = BeautifulSoup(contenido, 'lxml')
        
        
        
        for div in soup.find_all("div"):
            if(div.attrs['id'] == 'numeros_generados'):
                x = re.findall('[0-9]{2}\.[0-9]{2}', div.text)
                y = float (x[0])
                send_data_to_es(id, data = {"numero": y})
                id += 1
                break   
        
        time.sleep(segundos)


#--------------------------------------------------------------------------------------#

# Aqui creamos el thread.
# El primer argumento es el nombre de la funcion que contiene el codigo.
# El segundo argumento es una lista de argumentos para esa funcion .
# Ojo con la coma al final!
    
    
deleteIndex("numeros")
hilo = threading.Thread(target=ejecucion_horaria, args=(120,))
hilo.start()   # Iniciamos la ejecuci�n del thread,


#AQUÍ COMENZAMOS CON BEEBOTTE
bclient.write('dev','res1','y')
bclient.write('dev','res2','media')
bclient.publish('dev','res1','y' )
bclient.publish('dev','res2','media' )
records = bclient.read('dev', 'res1', limit = 5)
records = bclient.read('dev', 'res2', limit = 5)


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


@app.route('/logout')  
def logout(): 
  if 'nombre' in session:  
    session.pop('nombre',None)  
    return render_template('index.html');  
  else:  
    return '<p>el usuario ha cerrado su sesion</p>'  



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)