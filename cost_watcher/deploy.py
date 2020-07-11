import os
import shutil
import tempfile
import tarfile
import collections
import glob

import requests
import boto3

PackageRecord = collections.namedtuple('PackageRecord', 'url directories')

url_prefix = 'https://files.pythonhosted.org/packages/'

deps = {}

os.makedirs('codepkg')

with tempfile.TemporaryDirectory() as tempdir:
    for pkg, record in deps.items():
        filename = os.path.basename(record.url)
        print(f'Downloading {filename}...')
        r = requests.get(url_prefix + record.url)
        downloaded = os.path.join(tempdir, filename)
        with open(downloaded, 'wb') as f:
            f.write(r.content)
        with tarfile.open(downloaded, 'r') as t:
            t.extractall(tempdir)
        for d in record.directories:
            src = os.path.join(tempdir, filename.split('.tar.gz')[0], d)
            dest = os.path.join('codepkg', d)
            shutil.move(src, dest)

for p in glob.glob('*.py'):
    print(f'Packaging {p}')
    shutil.copy(p, 'codepkg')
shutil.make_archive('codepkg', format='zip', root_dir='codepkg', base_dir='.')

shutil.rmtree('codepkg')

client = boto3.client('lambda', region_name='us-west-2')
with open('codepkg.zip', 'rb') as f:
    r = client.update_function_code(
        FunctionName='XGBoostCICostWatcher',
        ZipFile=f.read(),
        Publish=False)
