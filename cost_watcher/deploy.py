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

deps = {
    'pytz': PackageRecord(
        url='f4/f6/94fee50f4d54f58637d4b9987a1b862aeb6cd969e73623e02c5c00755577/pytz-2020.1.tar.gz',
        directories=['pytz']),
    'chardet': PackageRecord(
        url='fc/bb/a5768c230f9ddb03acc9ef3f0d4a3cf93462473795d18e9535498c8f929d/chardet-3.0.4.tar.gz',
        directories=['chardet']),
    'idna': PackageRecord(
        url='ea/b7/e0e3c1c467636186c39925827be42f16fee389dc404ac29e930e9136be70/idna-2.10.tar.gz',
        directories=['idna']),
    'requests': PackageRecord(
        url='da/67/672b422d9daf07365259958912ba533a0ecab839d4084c487a5fe9a5405f/requests-2.24.0.tar.gz',
        directories=['requests']),
    'jenkinsapi': PackageRecord(
        url='e7/e7/c4bebfa8e50db11043dd28d0a9e142e70507a557517d0cea41437c9cb46e/jenkinsapi-0.3.11.tar.gz',
        directories=['jenkinsapi', 'jenkinsapi_utils'])
}

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
