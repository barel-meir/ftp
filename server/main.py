import os
import io
import shutil
from fastapi import FastAPI, File, UploadFile, Response
from fastapi.responses import FileResponse
from typing import List
from configparser import ConfigParser, ExtendedInterpolation, ConfigParser

from models import FileData, FileDataIn, FileDataOut
import zipfile
import uvicorn
import logging

# globals
app = FastAPI()
artifacts_path = ''
db: List[FileData] = []
responses = {
    404: {"description": "Item not found"},
    500: {"description": "My bad"}
}
config = ConfigParser(os.environ)


def save_artifact(artifact_data: FileData, artifact):
    try:
        logging.debug(f"saving {artifact_data.name} at {artifact_data.path}")
        with open(artifact_data.path, "wb") as buffer:
            shutil.copyfileobj(artifact.file, buffer)
    except Exception as ex:
        raise ex


def generate_artifact_path(artifact_name):
    global artifacts_path
    return os.path.join(artifacts_path, artifact_name)


def handle_new_file(file: UploadFile):
    try:
        logging.debug(f'handle input file: {file.filename}')
        file_data = FileData(name=file.filename, path=generate_artifact_path(file.filename))
        save_artifact(file_data, file)
        file_data.size = os.path.getsize(file_data.path)
        db.append(file_data)
        return file_data
    except Exception as ex:
        logging.error(f'(!) an exception occurred: {ex.args}')


def is_file_exist(file_name: str):
    logging.debug(f'searching file: {file_name}')
    for data in db:
        if data.name == file_name:
            logging.debug(f'found {file_name} in db')
            return True, data
    logging.error(f'could not find {file_name} in db')
    return False, None


def handle_get_file(file_name: str):
    logging.debug(f'handle request for file: {file_name}')
    is_exist, data = is_file_exist(file_name)
    if not is_exist:
        raise FileNotFoundError(file_name)
    return data


def zip_files(files_data: List[FileData]):
    zip_filename = "archive.zip"

    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")

    for data in files_data:
        fpath = data.path
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)

        # Add file, at correct path
        zf.write(fpath, fname)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })

    return resp


@app.get("/")
async def root():
    return True


@app.get("/list")
async def get_all_files():
    """
    :return: all files meta data in DB in the form of its name and size (data out model)
    """
    logging.debug("handle get_all_files")
    files = []
    for data in db:
        files.append(FileDataOut(name=data.name, size=data.size))
    return files


@app.get("/files", response_class=FileResponse)
async def get_file(files_data: List[FileDataIn]):
    """
    gets a list of files names, if the file exists in the server then it will be added to a zip archive, else it would
     be skipped.
    :return: a zip archive contains all of the valid requested files.
    """
    try:
        files: List[FileData] = []
        for file_name in files_data:
            try:
                data = handle_get_file(file_name.name)
                files.append(data)
            except FileNotFoundError as ex:
                logging.error(f'(!) could not find: {ex.args}')

        return zip_files(files)
    except Exception as ex:
        logging.error(f'(!) an exception occurred: {ex.args}')


@app.get("/file")
async def get_file(file_data: FileDataIn, response: Response):
    """
    gets a files name, if the file exists in the server then it will be sent back as response,
    else error 404 would be return
    :return: response contains the requested file.
    """
    try:
        data = handle_get_file(file_data.name)
        return FileResponse(data.path)
    except FileNotFoundError as ex:
        logging.error(f'(!) could not find: {ex.args}')
        response.status_code = 404
        response.body = responses[404]
        return responses[404]
    except Exception as ex:
        logging.error(f'(!) an exception occurred: {ex.args}')
        response.status_code = 500
        return file_data


@app.put("/file")
async def create_upload_files(files: List[UploadFile] = File(...)):
    """
    Get artifacts from the user, save them and update DB
    :param files: list of files
    :return: list of all the files meta data
    """
    files_data: List[FileData] = []
    for file in files:
        file_data = handle_new_file(file)
        files_data.append(file_data)
    return files_data


def create_artifacts_directory():
    """
    This method creates a folder on the server running this program.
    saves the files to the disk.
    """
    logging.debug("creating artifacts directory")
    home_path = os.path.dirname(os.path.realpath(__file__))
    artifacts_path = os.path.join(home_path, config['artifactory']['directory_name'])
    if not os.path.exists(artifacts_path):
        os.makedirs(artifacts_path)
    logging.debug("artifacts path: {0}".format(artifacts_path))
    return artifacts_path


def initiate_db():
    """
    initiates the connection to the DB when the program starts.
    Note: as for now it is not connected to any real DB I use the local artifacts path as
        some kind of a DB and read the data from it.
    """
    logging.debug("initiating db")
    for root, directories, files in os.walk(artifacts_path):
        for file in files:
            logging.debug(f"handle {file}")
            f_path = os.path.join(artifacts_path, file)
            db.append(FileData(name=file, size=os.path.getsize(f_path), path=f_path))


def initiate_server_connection():
    try:
        address = str(config['connection']['address'])
    except ...:
        logging.fatal("(!) please provide a valid address")
        exit(1)
    try:
        port = int(config['connection']['port'])
    except ...:
        logging.fatal("(!) please provide a valid port")
        exit(1)

    logging.info(f"starting server at {address}:{port}")
    uvicorn.run(app, host=address, port=port, ssl_keyfile="./key.pem", ssl_certfile="./cert.pem")


if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG)
        logging.info("FTP SERVER")
        logging.debug("initiating ftp server")
        logging.debug("initiating config file")
        config._interpolation = ExtendedInterpolation()
        config.read('config.ini')
        artifacts_path = create_artifacts_directory()
        initiate_db()
        initiate_server_connection()
    except Exception as ex:
        logging.error(f'(!) an exception occurred: {ex.args}')
