# GoSykel

GoSykel es una aplicación móvil que permite a los ciclistas registrarse y crear rutas así como realizar rutas creadas por otros usuarios. 

Los usuarios de GoSykel pueden obtener puntos realizando diferentes acciones como por ejemplo: registrar nuevas rutas, realizar rutas creadas por otros usuarios o añadir un nuevo tramo de carril bici. Dichos puntos se pueden usar para consultar la posición del usuario en el ranking de usuarios de la aplicación y canjearlos en una tienda donde pueden adquirir avatares, encabezados e insignias para personalizar su perfil. 

## Introducción
Este documento describe el proceso a seguir para instalar el servidor de la aplicación en su ordenador.

En este manual se detallan de forma clara y ordenada los pasos a seguir para instalar el
servidor web que emplea la aplicación en su ordenador.

Para completar los pasos que se describen posteriormente, es necesario que el sistema operativo de su ordenador sea Windows o Linux.

Si le surge cualquier duda o comentario, por favor no dude en enviar un email a esta [dirección](mgm7cns@uma.es).

## Pre-requisitos
Para ejecutar los pasos de este manual correctamente, se recomienda que  tenga el siguiente software instalado en su ordenador: 
- [Python](https://www.python.org/downloads/): durante el desarrollo se ha usado la versión 3.10.2
- [Postman](https://www.postman.com/)

## Instalación de dependencias

Clone el contenido de este repositorio.

El directorio donde ha clonado este repositorio contiene el código fuente del servidor.

Dentro del directorio, abra una terminal y ejecute el comando 
```bash
python -m venv <nombre-venv>
``` 
para crear un nuevo entorno virtual donde instalar todas las dependencias sin interferir con otras instalaciones que pudiera tener en su ordenador. 

Active el entorno virtual, para activarlo en Windows ejecute el comando 
```bash 
<nombre-venv>\Scripts\activate
``` 
o para activarlo en Linux ejecute el comando 
```bash
source <nombre-venv>/bin/activate
``` 


El entorno virtual está activo cuando en la línea de comandos le aparece lo siguiente:
```bash 
(nombre-venv) path\hacia\la\carpeta\GoSykel-Backend>
```

Use el paquete [pip](https://pip.pypa.io/en/stable/) para instalar las dependencias. Para ello ejecute: 
```bash 
pip install -r requirements.txt
```

## Configuración de Firebase
De cara a ejecutar el proyecto con sus credenciales de Firebase, por favor, siga los pasos de este [tutorial](https://cloud.google.com/firestore/docs/client/get-firebase) para crear un proyecto de Firebase y habilitar la autenticación con correo electrónico y contraseña. Es importante seleccionar la opción web a la hora de crear el proyecto en Firebase.

Además, si planea usar el servidor en combinación con la aplicación móvil desarrollada en React Native, le recomiendo que guarde la información de la configuración del proyecto de Firebase que acaba de crear. Por favor, diríjase al repositorio que contiene el código fuente de la aplicación móvil donde se le explicará como proceder.

Para [habilitar Firebase Admin SDK](https://firebase.google.com/docs/admin/setup) diríjase al proyecto que acaba de crear > Configuración del proyecto > Cuentas de servicio > Seleccionar Python > Generar nueva clave privada. 

Esto descargará un archivo JSON (serviceAccountKey.json) cuyo contenido debe copiar al archivo llamado ```firebase.py``` ubicado dentro de la carpeta ```firebase```. Una vez abra el archivo ```firebase.py``` reemplace los siguientes campos por la información disponible en el archivo JSON que acaba de guardar. 
```json
CERTIFICATE = {
  "type": "complete",
  "project_id": "complete",
  "private_key_id": "complete",
  "private_key": "complete",
  "client_email": "complete",
  "client_id": "complete",
  "auth_uri": "complete",
  "token_uri": "complete",
  "auth_provider_x509_cert_url": "complete",
  "client_x509_cert_url": "complete"
}
```

## Uso

Tenga en cuenta que el servidor se ejecutará en el puerto 5000, así que si tiene algún servicio ejecutándose en ese puerto, deténgalo.

Tras instalar las dependencias, para poner en marcha el servidor con el entorno virtual activo ejecute
```bash 
python app.py
```

Para comprobar que el servidor funciona como se espera, abra Postman y cree una nueva petición POST cuyo endpoint sea ```http://127.0.0.1:5000/users```. En el cuerpo de la petición POST complete la siguiente información 
```json
{
    "email": "completar",
    "nickname": "completar"
}
```
Esto creará un nuevo usuario, si todo ha ido bien le devolverá el ID del usuario que acaba de crear un token que deberá incluir en el header 'Authorization' en todas las peticiones que haga al servidor.

Si por el contrario desea obtener un token iniciando sesión tras haber creado un nuevo usuario previamente, realice una petición POST al endpoint ```http://127.0.0.1:5000/login```. En el cuerpo de la petición complete la siguiente información
```json
{
    "email": "completar"
}
```

Tras esta petición el servidor le devolverá el ID del usuario que acaba de iniciar sesión y el token correspondiente a dicho usuario y que deberá incluir en peticiones posteriores.

De cara a ser rigurosos con el ciclo de vida de los tokens, tras comprobar el funcionamiento del servidor en local debe hacer una petición GET al endpoint ```http://127.0.0.1:5000/logout``` indicando en el header 'Authorization' el token devuelto anteriormente.

Cuando termine de probar el servidor en local ejecute el comando ```Ctr + C``` para detener la ejecución del servidor. Si ha realizado cambios y los quiere probar en local, ejecute el comando ```Ctr + C``` y acto seguido inicie de nuevo el servidor con el comando ```python app.py```

Para desactivar el entorno virtual donde se estaba ejecutando el servidor anteriormente ejecute ```deactivate```. Este comando sirve tanto para Windows como para Linux.

## Despliegue en la nube 

Para desplegar los cambios que se realicen sobre el servidor se le ofrecen varias alternativas:
- [Firebase](https://firebase.google.com/docs/hosting)
- [Heroku](https://devcenter.heroku.com/articles/getting-started-with-python?singlepage=true)


Tras desplegar la aplicación en uno de esos dos proveedores se le asignará una URL para acceder a la aplicación. Guarde esta URL ya que será la que usará para probar los endpoints con Postman. Si quiere usar su propia versión del servidor en la aplicación móvil conserve la URL y diríjase al repositorio que contiene el código fuente de la aplicación móvil donde se le explicará como proceder.

## Contribuir
Se aceptan Pull Requests. Si desea hacer cambios mayores, abra un issue antes para conocer lo que le gustaría cambiar.
