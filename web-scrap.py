# My Web-Scrapping
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import os
from argparse import ArgumentParser, Action
import urllib.request as urllib2
import atexit
import datetime
import socket
import time
from urllib.error import URLError

files = []
print_items = 50
rootURL = ""
csvPath = ""

last_prlen = 0
def print_overlay(str):
    global last_prlen
    if (len(str) < last_prlen):
        print(f'\r{str}', ' '*(last_prlen-len(str)), end='\r')
    else:
        print(f'\r{str}', end='\r')
    last_prlen = len(str)
    
def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    print_overlay('%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix))

def get_percent(cur, total, precision=1):
    pcnt = 0.0
    if (cur == 0):
        pcnt = 0
    else:
        pcnt = round(cur*100/total, precision)
    return pcnt

def save_file_list(desc=''):
    if (desc != ''):
        print(desc)
    df = pd.DataFrame(files)
    df.to_csv(csvPath, index=False, encoding='utf-8')
    
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
    
    csv_column = list(ifile.keys())
    with open(csvPath, 'a', newline='') as csvfile:
        fieldnames = csv_column
        writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
        if (csvfile.tell() == 0):
            writer.writeheader()
        writer.writerow(ifile)
    print("added " + url)

def down_files():
    count = len(files)
    for i in range(0, count):
        if files[i]['downloaded'] == 'yes':
            continue
        url = files[i]['href']
        folder_flag = 1 if files[i]['type'] == 'folder' else 0
        pathlen = len(rootURL)
        filepath = "." + url[pathlen:]
        if (folder_flag == 1):
            files[i]['downloaded'] = 'yes'
            save_file_list()
            continue
        while(True):
            try:
                raw_url = url.replace("/blob/", "/raw/")
                u = urllib2.urlopen(raw_url, timeout=60)
                file_size = int(u.info()["Content-Length"])
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

                f = open(filepath, 'wb')
                file_name = raw_url.split('/')[-1]
                file_size_dl = 0
                block_sz = 8192
                while True:
                    try:
                        buffer = u.read(block_sz)
                    except Exception as e:
                        print(f"\n{e} Retrying ...")
                        continue
                    if not buffer:
                        break
                    file_size_dl += len(buffer)
                    f.write(buffer)
                    dlkb = int(file_size_dl / 1024)
                    totlkb = round(file_size / 1024, 2)
                    prog_desc = f"downloading {file_name} ({dlkb}/{totlkb} KB) {get_percent(file_size_dl, file_size)}%"
                    print_overlay(prog_desc)
                f.close()
                
                if (file_size_dl < file_size):
                    print(f"\nFile {file_name} was not fully downloaded.")
                    return

                files[i]['downloaded'] = 'yes'
                save_file_list()
                nowtime = datetime.datetime.now().strftime("%d/%m/%Y %H:%M");
                print_overlay(f"[({i}/{count}){get_percent(i, count, 2)}% ({nowtime})] {filepath} ({totlkb})\n")
                debug_prefix = f"({i}/{count})"
                print_progress(i, count, debug_prefix, decimals=2)
                break
            except URLError as error:
                if isinstance(error.reason, socket.timeout):
                    print(f'\nsocket timed out - URL {raw_url}')
                    
                else:
                    print(f'Some other url error happened ({error.reason})')
                print(f"[{i}({filepath})] Retrying ...")
                time.sleep(1)
                pass
            except Exception as e:
                print(f'\n{e}')
                return
            except:
                print("\nfailed to manipulate file {}!".format(url[:]))
                return
    if (i == count):
        print("\nCompleted!")
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
    else:
        atexit.register(save_file_list, "Save file list before exit...")
        down_files()

if __name__ == '__main__':
    main()
