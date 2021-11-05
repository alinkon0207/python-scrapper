# My Web-Scrapping
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from argparse import ArgumentParser, Action
import datetime

files = []
print_items = 50
rootURL = ""
csvPath = ""

def list_files(path, folder_flag):
    url = rootURL + path
# check if url exists in csv file

    try:
        for x in files:
            if (x['href'] == url):
                print("skipped " + url)
                return
        else:
            pass
    except Exception as e:
        print(str(e))
    finally:
        pass

# if it does not exist, send request
    if (folder_flag == 1):
        print("searching in " + url)
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.findAll('td', attrs={'class':'tree-item-file-name'})
        for item in items:
            if (item.contents[1].text == '..'): # skip '..' dir
                continue
            iclass = item.contents[1]['class'][1]
            href = item.contents[3]['href']
            if iclass == 'fa-folder':
                list_files(href, 1)
            else:
                list_files(href, 0)

    ifile = {}
    ifile['type'] = 'file' if folder_flag == 0 else 'folder'
    ifile['downloaded'] = "no"
    ifile['href'] = url

    files.append(ifile)
    df = pd.DataFrame(files)
    df.to_csv(csvPath, index=False, encoding='utf-8')

    print("added " + url)

def down_files():
    print("download started...")
    count = len(files)
    for i in range(0, count):
        print("(" + str(i) + "/" + str(count) + ")-" + files[i]['href'], end = '')
        if files[i]['downloaded'] == 'yes':
            print(" <---- checked")
            continue
        else:
            url = files[i]['href']
            folder_flag = 1 if files[i]['type'] == 'folder' else 0
            pathlen = len(rootURL)
            filepath = "." + url[pathlen:]

            if (folder_flag == 1):
                files[i]['downloaded'] = 'yes'
                df = pd.DataFrame(files)
                df.to_csv(csvPath, index=False, encoding='utf-8')
                continue
            try:
                raw_url = url.replace("/blob/", "/raw/")
                response = requests.get(raw_url)
                try:
                    dirpath = filepath
                    tmppath = "."
                    try:
                        while (True):
                            lastindex = dirpath.index("/", len(tmppath) + 1, -1)
                            if (lastindex < 0):
                                break
                            tmppath = dirpath[0: lastindex]
                            os.makedirs(tmppath, 0o777, True)
                    except:
                        pass

                    f = open(filepath, 'w+b')
                    f.write(response.content)
                    f.close()

                    files[i]['downloaded'] = 'yes'
                    df = pd.DataFrame(files)
                    df.to_csv(csvPath, index=False, encoding='utf-8')

                    print(" <---- downloaded: " + datetime.datetime.now())
                except Exception as e:
                    print(e)
                except:
                    print(" <---- failed to manipulate file {}!".format(url[:]))
            except:
                print(" <---- Failed at item ", i)
                break

def parse_int(x):
    return int(x, 0)

class ValidateStrLenAction(Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if 'maxlen' not in kwargs:
            raise ValueError('maxlen must be set')
        self.maxlen = int(kwargs['maxlen'])
        del kwargs['maxlen']
        super(ValidateStrLenAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) > self.maxlen:
            raise ValueError('String argument too long: max {0:d}, got {1:d}'.
                format(self.maxlen, len(values)))
        setattr(namespace, self.dest, values)

def parse_cmdline():
    parser = ArgumentParser()

    parser.add_argument('-root','--root_url', help='URL to root of website', default='', action=ValidateStrLenAction, maxlen=0x800, required=True)
    parser.add_argument('-url','--relative_url', help='URL to download', default='', action=ValidateStrLenAction, maxlen=0x800, required=True)
    parser.add_argument('-csv','--csv_path', help='csv file path to store the individual url items', default='', action=ValidateStrLenAction, maxlen=0x400, required=True)
    parser.add_argument('-w', '--write_csv', help='flag to write urls to a csv file', default=0, type=parse_int)

    return parser.parse_args()

def main():
    args = parse_cmdline()

    global rootURL
    global rootDN
    global csvPath
    global files

    rootURL = args.root_url
    csvPath = args.csv_path

    if (os.path.isfile(args.csv_path)):
        aa = pd.read_csv(args.csv_path)
        files = list(aa.T.to_dict().values())

    if (args.write_csv == 1):
        list_files(args.relative_url, 1)

    down_files()

# python web-scrap.py -root "https://gitlab.mingwork.com" -url "/hanguoliang/test/tree/PB1/wlan_proc" -csv "files.csv" -w 1

if __name__ == '__main__':
    main()
