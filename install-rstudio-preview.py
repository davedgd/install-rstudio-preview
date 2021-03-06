# To-Do:
# For Windows, need to check if RStudio is already running and quit (or install fails)
# Print current installed version (if applicable)
# Update for RStudio Preview 1.3? (not yet released; 1.2 now main release)

import requests

import urllib.request
from tqdm import tqdm

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from bs4 import BeautifulSoup as BS

import pandas as pd

import os
import platform
import distro

#print(distro.linux_distribution(full_distribution_name = False))

import subprocess

from urllib.parse import urlparse

import sys

###

def main():

    user_agent_rotator = UserAgent(software_names = SoftwareName.CHROME.value, operating_systems = OperatingSystem.WINDOWS.value, limit = 10)
    user_agent = user_agent_rotator.get_random_user_agent()

    headers = {'User-Agent': user_agent}

    page = requests.get('https://www.rstudio.com/products/rstudio/download/preview/', headers = headers)

    soup = BS(page.content.decode(), features="html.parser")

    tableRows = soup.find_all('table', {'class': 'table table-simple'})[0].find_all('td')

    tableIter = iter(tableRows)

    versions = []
    platforms = []
    urls = []

    for i, row in enumerate(tableIter):
        if i % 4 == 0:
            versions.append(row.find('a').text.split(' - ')[0].split(" ")[1].strip())
            platforms.append(row.find('a').text.split(' - ')[1].strip())
            urls.append(row.find('a').get('href'))

    #print(urls)

    df = pd.DataFrame(data = {'Platform': platforms, 'Version': versions, 'Selection': range(1, len(urls) + 1), 'URL': urls})

    match = False

    if len(sys.argv) > 1:
        for eachPlatform in platforms:
            if sys.argv[1].replace('"', '').replace("'", '') in eachPlatform:
                match = True

    if match:
        toInstall = int(df[df['Platform'].str.contains(sys.argv[1].replace('"', '').replace("'", ''))].index.values.astype(int))
    else:

        print('\r')

        print(df.iloc[:,0:3].to_string(index = False))

        while True:
            try:
                print('\nEnter selection number to install (or 0 to quit):', end = " ")
                toInstall = int(input())
                if toInstall in range(0, len(urls)):
                    toInstall = toInstall - 1
                    break
                elif toInstall == 0:
                    print('Installation cancelled...')
                    toInstall = -1
                    break
            except:    
                pass

            print('Your selection is invalid (type 0 to cancel)!')

        if toInstall == -1:
            exit()

    print('\nYou selected:', df.iloc[toInstall, 0])

    selectedUrl = df.iloc[toInstall, 3]

    # progress bar thanks to https://stackoverflow.com/a/53877507

    class DownloadProgressBar(tqdm):
        def update_to(self, b=1, bsize=1, tsize=None):
            if tsize is not None:
                self.total = tsize
            self.update(b * bsize - self.n)

    def download_url(url, output_path):
        with DownloadProgressBar(unit='B', unit_scale=True,
                                miniters=1, desc=url.split('/')[-1]) as t:
            urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

    file = os.path.basename(urlparse(selectedUrl).path)

    if 'Ubuntu' in df.iloc[toInstall, 0]:

        pipe = subprocess.Popen('apt-cache policy rstudio', shell = True, stdout = subprocess.PIPE).stdout

        try:
            version = str(pipe.read()).split('\\n')[1].split('Installed: ')[1]
        except:
            version = None

        if version != df.iloc[toInstall, 1]:
            print('Installing...')
            download_url(selectedUrl, output_path = os.path.join(os.getcwd(), file))
            subprocess.run(["sudo", "dpkg", "-i", file])
            os.remove(file)
            print('Installation complete!')
        else:
            print('\nYou are already using the latest version (' + version + ')! Aborting...', sep = '')
            quit()

    elif 'Windows' in df.iloc[toInstall, 0]:

        version = subprocess.check_output('wmic datafile where name="C:\\\\Program Files\\\\RStudio\\\\bin\\\\rstudio.exe" get version', stderr = subprocess.PIPE).decode().split('\r\r\n')[1].strip()

        if (df.iloc[toInstall, 1] in version):
            print('\nYou are already using the latest version (' + version + ')! Aborting...', sep = '')
            quit()
        else:
            print('Installing...')
            download_url(selectedUrl, output_path = os.path.join(os.getcwd(), file))
            subprocess.run([file, "/S"])
            os.remove(file)
            print('Installation complete!')

    elif 'macOS' in df.iloc[toInstall, 0]:

        try:
            version = str(subprocess.check_output('cat /Applications/RStudio.app/Contents/Info.plist | grep -A1 CFBundleShortVersionString | grep string | sed "s/<[^>]*>//g"', shell = True, stderr = subprocess.PIPE)).split('\\t')[1].split('\\n')[0]
        except:
            version = None

        if (df.iloc[toInstall, 1] == version):
            print('\nYou are already using the latest version (' + version + ')! Aborting...', sep = '')
            quit()
        else:
            print('Installing...')
            download_url(selectedUrl, output_path = os.path.join(os.getcwd(), file))

            subprocess.call('hdiutil attach ' + file + '; rm -rf /Applications/RStudio.app; ' + 'cp -R /Volumes/' + os.path.splitext(file)[0] + '/RStudio.app /Applications; hdiutil detach /Volumes/' + os.path.splitext(file)[0], shell = True, stdout = subprocess.DEVNULL)
            
            os.remove(file)
            print('Installation complete!')

if __name__== "__main__":
  main()