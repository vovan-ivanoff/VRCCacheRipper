import os
from pathlib import Path
import re
import shutil
import subprocess
import vrchatapi
from vrchatapi.api import authentication_api,avatars_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode
import atexit
import argparse
import sys
import json
from threading import Thread,Lock

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
parser.add_argument("-j","--j", type=int,help="how many threads to use(default=4)", required=False, default=4)
parser.add_argument("-mins","--minsize", type=int,help="mminimum size of avatar in MB(default 0MB)", required=False, default=0)
parser.add_argument("-asr","--assetripper", type=str,help="path to assetripper.exe", required=False, default="./AssetRipper.exe")
parser.add_argument("-clsf","--classify", action="store_true",help="dont unpack, only classifu and name", required=False)
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
        # Step 3. Calling getCurrentUser on Authentication API logs you in if the user isn't already logged in.
        current_user = api_instance.get_current_user()
    except ValueError as e:
        # Step 3.5. Calling verify2fa if the account has 2FA enabled
        api_instance.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(input("2FA Code: ")))
        current_user = api_instance.get_current_user()
    except UnauthorizedException as e:
        if UnauthorizedException.status == 200:
            # Step 3.5. Calling verify2fa if the account has 2FA enabled
            authentication_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(input("2FA Code: ")))
            current_user = authentication_api.get_current_user()
        else:
            print("Exception when calling API: %s\n", e)
    except vrchatapi.ApiException as e:
        print("Exception when calling API: %s\n", e)


    #все, залогинились, идем дальше

pathes = []
valid = []
cnt =0
ctr =0 
lock = Lock()

pattern_a=re.compile(rb"prefab-id-v1_avtr_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
pattern_w=re.compile(rb"wrld_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
def get_id(file):
    with open(file,"rb") as f:
        s=f.read()
        res=pattern_a.findall(s)
        if len(res)==2:
            return "avtr_"+str(res[0])[2:-1:]
        else:
            try:
                return "wrld_"+str(pattern_w.findall(s)[0])[2:-1:]
            except:
                return None



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


def getname_a(id):                    #тут мы обращаемся к api и выделяем имя аватара
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


def run_asr(tsk,lst):
    global ctr
    for o in  range(len(tsk)):
        
        dst= outputDir +f"\{lst[tsk[o]]}"
        out= f'{outputDir}\exported\{lst[tsk[o]]}'
        r = subprocess.run([assetripperPath, dst,'-o',out],input='\n', encoding='ascii',stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        while lock.locked():
            pass #wait to unlock lock by other thread
        with lock:
            ctr+=1
        if ctr%args.j == 0 and ctr//args.j <= cnt:
            print(f"Unpacked: {ctr//args.j} files, {((ctr//args.j)*100/cnt):0.2f}%")


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
        name=get_id(valid[i])
        if name != None:
            dst = outputDir +"\\"+name
            procent = (i+1) / len(valid)*100
            shutil.copy(valid[i], dst)
            print(f"exported:{procent:0.2f}% ({i+1} files)")

def unpackIt():
        global cnt
        thr=[]
        ld= os.listdir(outputDir)
        tasks=[[]]*args.j #create threads task list
        #for y in range(args.j-1):
        #    tasks[y].append([None])
        cnt=len(ld)-1
        for i in range(cnt):         #создаем папки и распаковываем туда .vrca с помощью ассетриппера
            #split by threads:
            tasks[i%(args.j)].append(i)
            print(tasks[0])
            #print(outputDir+f"\exported\{i}")
            try:
                os.mkdir(outputDir+f"\exported\{ld[i]}")
            except FileExistsError:
                pass
            except FileNotFoundError:
                os.mkdir(outputDir+"\exported")
                os.mkdir(outputDir+f"\exported\{ld[i]}")
            #print([assetripperDir, dst,f'-o {outputDir}\exported\{i}'])
        for l in range(args.j):
            thr.append(Thread(target=run_asr,args=[tasks[l],ld]))
            thr[l].start()
        for x in range(args.j):
            thr[x].join()
        #print(f"Unpacked:{procent:0.2f}% ({i+1} files)")


def nameIt():
    for f in os.listdir(outputDir):
        print(f) #из распакованных папок берем avtr_id, через vrchat api запрашиваем имя аватара, если получаем ответ то переименовываем папку
        #if str(f).startswith("avtr"):
        avatar_name = getname_a(f)
        if(avatar_name != None):
            try:
                print(f+" name: "+avatar_name)
                os.rename(outputDir+"\\"+f, outputDir+"\\"+get_valid_filename(avatar_name))
            except PermissionError as e:
                pass
            except FileExistsError as e:
                pass

def classify(src):
    avat = src + "\ExportedProject\Assets\Avatar"
    ls=os.listdir(avat)
    for str in ls:
        if "Nardo" in str:
            return "(nardo)_"
        elif "Re" in str:
            return "(rex)_"
        elif "Wicker" in str:
            return "(wicker)_"
        elif "Can" in str:
            return "(canine)_"
        elif "Taidum" in str:
            return "(taidum)_"
        elif "Angel" in str:
            return "(dutchie)_"
        elif "Pro" in str:
            return "(proto)_"
        elif "avali" in str:
            return "(avali)_"
        else:
            pass
    anim = src + "\ExportedProject\Assets\AnimationClip"
    ls = os.listdir(anim)
    for str in ls:
        if "dragon" in str:
            return "(nardo)_"
        elif "rex" in str:
            return "(rex)_"
        else: return ""
    tex = src + "\ExportedProject\Assets\Texture2D"
    ls = os.listdir(tex)
    for str in ls:
        if "dragon" in str:
            return "(nardo)_"
        elif "Rex" in str:
            return "(rex)_"
        else: return ""

def classifyIt():
    wd = outputDir+"\exported\\"
    files = os.listdir(wd)
    for i in range(0,len(files)):
        try:
            speicie = classify(wd+files[i])
            os.rename(wd+files[i], wd+speicie+files[i])
        except PermissionError as e:
            print('renaming failed', e)
            f = open(outputDir+f"\exported\__Names.txt", "a")
            f.write(str(f'{i}:type: {speicie}\n'))
            f.close()
            pass
        except Exception as e:
            pass

       

print("strating...(This Might take a while.....)")
if not args.classify:
    exportIt()
    nameIt()
    unpackIt()
classifyIt()

