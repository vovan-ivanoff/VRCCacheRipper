import os
from pathlib import Path
import re
import shutil
import subprocess
import vrchatapi
from vrchatapi.api import authentication_api,avatars_api
import atexit
import argparse
import sys
import json


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

parser = MyParser()
parser.add_argument("-o","--output", type=str,help="output path for unpacking avatars", required=True)
parser.add_argument("-i","--input", type=str,help="path to cache of vrchat(Cache-WindowsPlayer)")
parser.add_argument("--nonaming", action="store_true",help="wether or not name avatars", required=False)
parser.add_argument("-u","--username", type=str,help="username of vrc account for avatar naming, if you dont want use this, use --nonaming",required=not '--nonaming' in sys.argv)
parser.add_argument("-p","--password", type=str,help="password of vrc account for avatar naming, if you dont want use this, use --nonaming",required=not '--nonaming' in sys.argv)
parser.add_argument("-v","--verbose", action="store_true",help="verbose the output", required=False)
parser.add_argument("-s","--size", type=int,help="maximum size of avatar in MB(default 60MB)", required=False, default=60)
parser.add_argument("-mins","--minsize", type=int,help="mminimum size of avatar in MB(default 0MB)", required=False, default=0)
parser.add_argument("-asr","--assetripper", type=str,help="path to assetripper.exe", required=False, default="./AssetRipper.exe")
args = parser.parse_args()


if not args.nonaming:
    configuration = vrchatapi.Configuration(
        username = args.username,
        password = args.password,
    )
    
    #логинимся в аккаунт vrchat для обращения к api
    api_client = vrchatapi.ApiClient(configuration)
    api_instance = authentication_api.AuthenticationApi(api_client) 
    try:
        # Login and/or Get Current User Info
        api_response = api_instance.get_current_user()
        print('Logged in as: ' + api_response.display_name)
    except vrchatapi.ApiException as e:
        print("Exception when calling AuthenticationApi->get_current_user: %s\n" % e)
    #все, залогинились, идем дальше

pathes = []
valid = []

def getCachePath(): #ищем путь к кешу и если не находи, то кидаем эксепшон
    path = os.getenv('APPDATA')
    path = path.removesuffix("\Roaming")
    path+="\LocalLow\VRChat\VRChat"
    try:
        os.listdir(path+"\Cache-WindowsPlayer")
        Cachepath = path+"\Cache-WindowsPlayer"
    except:
        try:
            f =open(path+"\config.json","r")
            res= ''
            for i in f.read().splitlines():
                res+=i
            f.close()
            Cachepath =json.loads(res)["cache_directory"] +"\Cache-WindowsPlayer"
        except (FileNotFoundError, KeyError):
            Cachepath = None
    if Cachepath == None:
        raise FileNotFoundError("Script can't find VRChat Cache folder automatically! try using with '-i [path to Cache-Windows-Player]'")
    else:
        return Cachepath

def goodbye():                      #функция выхода, выходим из аккаунта vrchat (иначе плохо всё кончится)
    if not args.nonaming:
        api_instance = authentication_api.AuthenticationApi(api_client)
        # example, this endpoint has no required or optional parameters
        try:
            # Logout
            api_response = api_instance.logout()
            print(api_response)
        except vrchatapi.ApiException as e:
            print("Exception when calling AuthenticationApi->logout: %s\n" % e)
    print("CacheRipper Finished... Goodbye!")
atexit.register(goodbye)        #биндим эту функцию на выход


if args.input == None:
    cacheDir=getCachePath()+"\\"
else:  
    cacheDir=args.input+"\\"
outputDir =args.output
assetripperPath = args.assetripper
asr = Path(assetripperPath)
if asr.exists():
    pass
else:
    print("Cant find assetripper.exe! to get it download it from https://github.com/AssetRipper/AssetRipper/releases/tag/0.2.4.0 , unpack zip and put this script into extracted folder")
    raise FileNotFoundError("Cant find AssetRipper! Put this script into AssetRipper folder, or use '-asr [path to AssetRipper.exe]'")


def get_valid_filename(s):          #превращаем имена в нормальные
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def getname(id):                    #тут мы обращаемся к api и выделяем имя аватара
    # Instantiate instances of API classes
    api_instance = avatars_api.AvatarsApi(api_client)
    avatar_id = id # str | 
    try:
        api_response = api_instance.get_avatar(avatar_id)
        #print(api_response)
        a = str(api_response).split("\n")
        name = ''
        for i in a:
            if i.startswith(" 'name'"):
                name =i.split(":")[1][2:-2]
                break
        #print(name)
        return name
    except vrchatapi.ApiException as e:
        #print(f"Exception when calling API: {e}")
        return None


def get_path(dir):          #ммм, рекурсия :3
    l = os.listdir(dir)
    for d in l:
        try:
            get_path(dir +'\\'+d)
        except NotADirectoryError:
            pathes.append(dir)
            return
            
def exportIt():
    directories = os.listdir(cacheDir) #рекурсивно ищем папки в кеше vrchat'а
    #print(directories)
    get_path(cacheDir)
    for i in reversed(pathes):
        if os.listdir(i) == []:
            pathes.remove(i)
    pathes.pop(-1)

    for p in pathes:                    #из всех файлов выбираем предположительно аватары
        for j in os.listdir(p):
            size =os.path.getsize(p+'\\'+j)
            if(size > (100+(args.minsize *1000000)) and size < args.size *1000000):
                valid.append(p+'\\'+j)
    #print(valid)

    print(f"found {len(valid)} files")
    for i in range(len(valid)):         #переименовываем файл аватара __data  в .vrca и копируем в папку для экспорта
        dst = outputDir +f"\{i}.vrca"
        procent = (i+1) / len(valid)*100
        shutil.copy(valid[i], dst)
        print(f"exported:{procent:0.2f}% ({i+1} files)")

def unpackIt():
    for i in range(len(valid)):         #создаем папки и распаковываем туда .vrca с помощью ассетриппера
        dst = outputDir +f"\{i}.vrca"
        procent = (i+1) / len(valid)*100
        #print(outputDir+f"\exported\{i}")
        try:
            os.mkdir(outputDir+f"\exported\{i}")
        except FileExistsError:
            pass
        except FileNotFoundError:
            os.mkdir(outputDir+"\exported")
            os.mkdir(outputDir+f"\exported\{i}")
        #print([assetripperDir, dst,f'-o {outputDir}\exported\{i}'])
        if args.verbose:
            r = subprocess.run([assetripperPath, dst,f'-o', f'{outputDir}\exported\{i}'],input='\n', encoding='ascii')
        else:
            r = subprocess.run([assetripperPath, dst,f'-o', f'{outputDir}\exported\{i}'],input='\n', encoding='ascii',stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        print(f"Unpacked:{procent:0.2f}% ({i+1} files)")


def nameIt():
    f = open(outputDir+f"\exported\__Names.txt", "w")   #чистим файлик
    f.write('') 
    f.close()
    for i in range(len(valid)): #из распакованных папок берем avtr_id, через vrchat api запрашиваем имя аватара, если получаем ответ то переименовываем папку
        try:
            src = outputDir+f"\exported\{i}\ExportedProject\Assets\Asset_Bundles"
            id = os.listdir(src)[0]
            
            if not args.nonaming:
                #print(f"{i}: "+id)
                if id != "customavatar.unity3d":
                    id = id.removeprefix("prefab-id-v1_")
                    id = id.removesuffix(".prefab.unity3d")
                    arr =id.split("_")
                    id = arr[0]+"_"+arr[1]
                    avatar_name = getname(id)
                    if(avatar_name != None):
                        try:
                            print(f'{i}: '+id +" name: "+avatar_name)
                            os.rename(outputDir+f"\exported\{i}", outputDir+f"\exported\{get_valid_filename(avatar_name)}")
                        except PermissionError as e:
                            print('renaming failed', e)
                            f = open(outputDir+f"\exported\__Names.txt", "a")
                            f.write(str(f'{i}:name: {get_valid_filename(avatar_name)}\n'))
                            f.close()
                        except FileExistsError as e:
                            os.rename(outputDir+f"\exported\{i}", outputDir+f"\exported\{avatar_name}_1")
        except FileNotFoundError:
            os.rename(outputDir+f"\exported\{i}", outputDir+f"\exported\world_{i}")

def classify(src):
    path = src + "\ExportedProject\Assets\AnimationClip"
    ls=os.listdir(path)
    if "dragon_hands_fist.anim" in ls:
        return "nardo"
    elif "rex_hands_fist.anim" in ls:
        return "rex"
    else:
        return ""

def classifyIt():
    wd = outputDir+"\exported\\"
    files = os.listdir(wd)
    for i in range(0,len(files)):
        try:
            speicie = classify(wd+files[i])
            os.rename(wd+files[i], wd+f"({speicie})_"+files[i])
        except:
            pass

       

print("strating...(This Might take a while.....)")
exportIt()
unpackIt()
nameIt()
classifyIt()

