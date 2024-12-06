import sys
import base64
import struct
import requests
from PIL import Image

class SyntaxException(Exception):
    def __init__(self,msg: str):
        self.msg = msg

def http_request(method: str,string: str,json: dict,printResponse: bool = True) -> dict:
    print(f"Request: {string}")
    url = f"http://127.0.0.1:8080/{string}"
    response = None
    if method == "get":
        response = requests.get(url = url,json = json)
    elif method == "post":
        response = requests.post(url = url,json = json)
    elif method == "delete":
        response = requests.delete(url = url,json = json)
    assert response != None
    data = response.json()
    if printResponse:
        print(f"Response: {data}")
    return data

def cmd_exit(name,*args):
    if len(args) != 0:
        raise SyntaxException("Syntax: exit")
    sys.exit(0)

def cmd_addevent(name,*args):
    if len(args) != 1:
        raise SyntaxException("Syntax: addevent <event_name>")
    http_request("post","event",{"event_name": args[0]})

def cmd_delevent(name,*args):
    if len(args) != 2:
        raise SyntaxException("Syntax: delevent <user_token> <admin_token>")
    http_request("delete",f"event/{args[0]}",{"admin_token": args[1]})

def cmd_checkevent(name,*args):
    if len(args) != 1:
        raise SyntaxException("Syntax: checkevent <user_token>")
    http_request("get",f"event/{args[0]}",{})

def cmd_auth(name,*args):
    if len(args) != 1 and len(args) != 2:
        raise SyntaxException("Syntax: auth <user_token> [admin_token]")
    if len(args) == 1:
        http_request("post",f"auth/{args[0]}",{})
    else:
        http_request("post",f"auth/{args[0]}",{"admin_token": args[1]})

def flatten_list_of_iterables(data):
    return [y for x in data for y in x]

def cmd_addimage(name,*args):
    if len(args) != 2 and len(args) != 3:
        raise SyntaxException("Syntax: addimage <user_token> <path_to_image> [title]")
    with Image.open(args[1]) as file:
        if file.mode != "RGB" and file.mode != "RGBA":
            raise RuntimeError("Only RGB and RGBA files are supported.")
        title = "" if len(args) == 2 else args[2]
        pixels = bytearray(flatten_list_of_iterables([(pixel[0],pixel[1],pixel[2]) for pixel in file.getdata()]))
        pixelString = base64.b64encode(pixels).decode("utf-8")
        http_request("post",f"images/{args[0]}",{"pixels": pixelString,"width": file.width,"height": file.height,"title": title})

def cmd_getimage(name,*args):
    if len(args) != 2 and len(args) != 3:
        raise SyntaxException("Syntax: getimage <user_token> <image_id> [image_output_path]")
    content = http_request("get",f"images/{args[0]}/{args[1]}",{},False)
    if content["success"] == False:
        return
    images = content["params"]
    for image in images:
        width = int(image["width"])
        height = int(image["height"])
        element = {"image_id": image["image_id"],"title": image["title"],"width": width,"height": height}
        print(str(element))
        if len(args) != 3 or len(images) > 1:
            continue
        pixels = base64.b64decode(str(image["pixels"]).encode("utf-8"))
        Image.frombytes(mode = "RGB",size = (width,height),data = pixels).save(args[2])

def cmd_delimage(name,*args):
    if len(args) != 3:
        raise SyntaxException("Syntax: delimage <user_token> <image_id> <admin_token>")
    http_request("delete",f"images/{args[0]}/{args[1]}",{"admin_token": args[2]})

if __name__ == "__main__":
    commands = {
        "exit": cmd_exit,
        "addevent": cmd_addevent,
        "delevent": cmd_delevent,
        "checkevent": cmd_checkevent,
        "auth": cmd_auth,
        "addimage": cmd_addimage,
        "delimage": cmd_delimage,
        "getimage": cmd_getimage
    }
    while True:
        splitCmd = input("cmd: ").strip().split(" ")
        cmd = splitCmd[0]
        if cmd in commands:
            try:
                commands[cmd](*splitCmd)
            except SyntaxException as error:
                print(error.msg)
            except Exception as error:
                print(str(error))
        else:
            print(f"Command \"{cmd}\" doesn't exist.")
