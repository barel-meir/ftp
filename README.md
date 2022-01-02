# ftp
FTP server written in python FastAPI and client written in python 

# Server
the server is built using fastapi (https://fastapi.tiangolo.com/)
in the 'connfig.ini' file you should provide:
* the address and port the server should listen to. 
* the artifacts folder name to save the files in.

the server supports the following REST actions: 
* GET /list : returns a list of all the files meta data (name and size) that are saved in the db.
```
example:
curl -X 'GET' \
  'http://127.0.0.1:8000/list' \
  -H 'accept: application/json'
```
* GET /file : gets a file name and returns the file (binary).
```
{
  "name": "string"
}

example:
curl -X 'GET' \
  'http://127.0.0.1:8000/file' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "string"
}'
```
* GET /files : gets a list of files names and returns the files as a zip file (binary)
**Note:** the zip contains onky valid files that are stored in the server.
```
[
  {
    "name": "string"
  }
]

example:
curl -X 'GET' \
  'http://127.0.0.1:8000/files' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "name": "string1"
  },
  {
    "name": "string2"
  }
]'
```
* PUT /file : upload files to the server 
```
ecample:
curl -X 'PUT' \
  'http://127.0.0.1:8000/file' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@bb.png;type=image/png'
```

# Client
the cliennt is built in python using requests lib
in the 'config.ini' file you should provide:
* the address and port the client should connect to. 
* the artifacts folder name to save the files in (downloaded).

the ui of the app is a simple cli which gives the user the following options:
* exit
* get list of all files       
* download artifacts               
* upload artifacts 
* download all artifacts from server

