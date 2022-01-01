import os
import json
import logging
import zipfile
import requests
import platform
import uuid
from configparser import ExtendedInterpolation, ConfigParser

class Server:
    ip: str = None
    port: int = None
    base_url = None

#globals
config = ConfigParser(os.environ)
artifacts_path = ''
operations_dict = {
        0: "exit",
        1: "get list of all files",
        2: "download artifacts",
        3: "upload artifacts"
}
yes_no_dict = {0: "No", 1: "Yes"}

def read_int(message=''):
    res = None
    while res is None:
        try:
            res = int(input(message))
        except Exception:
            printer("Please enter valid numeric port number ", 3)
    return res

def read_bool(message=''):
    res = None
    while res is None:
        try:
            res = pick_from_map(yes_no_dict, message=message, print_map=False)
        except Exception:
            printer("Please enter valid option ", 3)
    return res[0] == 1


def pick_from_map(map, message=None, print_map=True):
    if message:
        printer(message)
    else:
        printer("Please pick the desired option: ")
    if print_map:
        print(map)
    for k in map.keys():
        print(f'{k} : {map[k]}')
    retVal = read_int()
    while retVal not in map.keys():
        printer("Please enter a valid option", severity=1)
        retVal = read_int()

    return retVal, map[retVal]


def printer(message, severity=0):
    if severity == 0:
        logging.debug(message)
    elif severity == 1:
        logging.info(message)
        print(message)
    else:
        logging.error(message)
        print(message)


def _save_artifact(f_name: str, artifact):
    try:
        f_path = _generate_artifact_path(f_name)
        logging.debug(f"saving {f_name} at {f_path}")
        with open(f_path, "wb") as buffer:
            buffer.write(artifact)
            buffer.close()
        return f_path
    except Exception as ex:
        raise ex


def _generate_artifact_path(artifact_name):
    global artifacts_path
    return os.path.join(artifacts_path, artifact_name)


def create_artifacts_directory():
    """
    This method creates a folder on the client running this program.
    saves the files to the disk.
    """
    global artifacts_path
    logging.debug("creating artifacts directory")
    home_path = os.path.dirname(os.path.realpath(__file__))
    artifacts_path = os.path.join(home_path, config['artifactory']['directory_name'])
    if not os.path.exists(artifacts_path):
        os.makedirs(artifacts_path)
    logging.debug("artifacts path: {0}".format(artifacts_path))


def initiate_connection():
    printer("initiating ftp server connection")
    server = Server()
    try:
        server.ip = str(config['connection']['address'])
    except ...:
        server.ip = input("Please enter the server address: ")
    try:
        server.port = int(config['connection']['port'])
    except ...:
        server.port = read_int("Please enter the server address: ")

    server.base_url = "http://{}:{}/".format(server.ip, server.port)
    printer(f"initiating connection to {server.base_url}")
    return server


def _test_connection(server):
    printer(f"testing connection to {server.base_url}")
    payload = {}
    headers = {}
    response_code = requests.request("GET", server.base_url, headers=headers, data=payload).status_code
    if response_code == 200:
        printer(f"successful connection to {server.base_url}", 1)
    else:
        printer(f'(!) could not connect to server! {server.base_url}, status code: {response_code}', 3)

    return response_code == 200


def _exit():
    print("bye bye (:")
    exit()


def get_list_of_all_artifacts(server):
    try:
        printer(f"get  list of all artifacts")
        url = server.base_url + "list"
        payload = {}
        headers = {}
        response = requests.get(url=url, headers=headers, data=payload)
        printer("artifacts:", 1)
        json_data = json.loads(response.text)
        printer(json_data, 1)
    except Exception as ex:
        printer(f'(!) an exception occurred: {ex.args}', 3)


def upload_artifact(server):
    """
    gets from the user the pats of the desired files to upload
    Note: this method assums the file is exists and valid
    :param server: the server to upload to
    """
    try:
        # """
        # EXAMPLE FOR SENDING FILES
        # f_name = '2'
        # f_path = r'C:\Users\tc10076\Desktop\tmp\ssssssss\2.txt'
        # data = {
        #     "files": (f_name, open(f_path, 'rb'))
        # }
        # """
        printer(f"upload artifacts")
        files_to_upload_paths = []
        is_to_enter_more_files = True
        files_counter = 1
        printer(f"Please enter the paths of the files you want to upload", 1)
        while is_to_enter_more_files:
            files = input(f"file {files_counter} path: ")
            for f in files.split():
                files_to_upload_paths.append(f)
                files_counter += 1
            is_to_enter_more_files = read_bool("Would you like to upload more files?")

        files_to_upload_tuples = []
        for f_path in files_to_upload_paths:
            f_name = f_path.split('\\')[-1] if platform.system() == 'Windows' else f_path.split('/')[-1]
            files_to_upload_tuples.append((f_name, open(f_path, 'rb')))
            printer(f"uploading {f_name} from {f_path} ...")
            data = {
                "files": (f_name, open(f_path, 'rb'))
            }
            response = requests.put(url=server.base_url + "file",
                                    files=data,
                                    )
            json_data = json.loads(response.text)
            printer(json_data, 1)

    except Exception as ex:
        printer(f'(!) an exception occurred: {ex.args}', 3)


def handle_archive_download(content):
    temp_zip_name = "{}{}".format(uuid.uuid4(), '.zip')
    path_to_zip_file = _save_artifact(temp_zip_name, content)
    printer(f"extracting zip {temp_zip_name} at {artifacts_path}")
    with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
        zip_ref.extractall(artifacts_path)

    printer(f"delete zip: {temp_zip_name}")
    os.remove(path_to_zip_file)


def download_multiple_artifacts(server, files_to_download_names):
    try:
        files_to_upload_tuples = []
        for f_name in files_to_download_names:
            files_to_upload_tuples.append({"name": f_name})

        data = json.dumps(files_to_upload_tuples)
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.get(url=server.base_url + "files",  headers=headers, data=data)
        if response.status_code == 200:
            handle_archive_download(response.content)
        else:
            printer(f"failed to download {files_to_download_names}", 3)
    except Exception as ex:
        printer(f'(!) an exception occurred: {ex.args}', 3)


def download_single_artifact(server, file_to_download_name):
    try:
        data = json.dumps({"name": file_to_download_name})

        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.get(url=server.base_url + "file", headers=headers, data=data)

        if response.status_code == 200:
            _save_artifact(file_to_download_name, response.content)
        elif response.status_code == 404:
            printer(f"file {file_to_download_name} is not found in server")
        else:
            printer(f"failed to download {file_to_download_name}")
    except Exception as ex:
        printer(f'(!) an exception occurred: {ex.args}', 3)


def download(server):
    printer(f"download artifacts from server")
    is_to_enter_more_files = True
    files_counter = 1
    files_to_download_names = []
    printer(f"Please enter the names of the files you want to download", 1)
    while is_to_enter_more_files:
        files = input(f"file {files_counter} name: ")
        for f in files.split():
            files_to_download_names.append(f)
            files_counter += 1
        is_to_enter_more_files = read_bool("Would you like to download more files?")

    if len(files_to_download_names) == 1:
        download_single_artifact(server, files_to_download_names[0])
    else:
        download_multiple_artifacts(server, files_to_download_names)


def cli():
    server = initiate_connection()
    if not _test_connection(server):
        if pick_from_map(map=yes_no_dict, message="Would you like to exit?"):
            _exit()
        else:
            cli()

    while True:
        print("=====================================================================")
        printer("Please pick operation", severity=1)
        op, text = pick_from_map(map=operations_dict, message="Please pick operation")
        if op == 1:
            get_list_of_all_artifacts(server)
        elif op == 2:
            download(server)
        elif op == 3:
            upload_artifact(server)
        else:
            _exit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    printer("FTP CLIENT", 1)
    logging.debug("initiating config file")
    config._interpolation = ExtendedInterpolation()
    config.read('config.ini')

    create_artifacts_directory()
    cli()
