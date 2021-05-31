import json
import os
import subprocess
import requests
from urlparse import urlparse
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3.exceptions import SNIMissingWarning

username = 'trends'
password = 'RXSK73sMJSwbS6eYdZZ5'


def disable_python_requests():
  """
  """
  requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
  requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
  requests.packages.urllib3.disable_warnings(SNIMissingWarning)
  return

def get_test_log_path(local_drt_mount_point, local_osl_mount_point, test_id):
  url = 'https://jita.eng.company.com/api/v1/agave_test_results/%s' % test_id
  comp_resp = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False)
  test_data = json.loads(comp_resp.content)
  test = test_data['data']
  test_name = test['test']['name']
  test_name_url = test_name.replace('.','/')
  agave_task = test['AgaveTask']['_id']['$oid']
  test_log_url = test['test_log_url']
  parsed_url = urlparse(test_log_url)
  test_log_path = parsed_url.path
  test_base_log_path = local_osl_mount_point + test_log_path
  if test["container_details"]["tester"]["lab"] == "drt":
    test_base_log_path = local_drt_mount_point + test_log_path
  if os.path.exists(test_base_log_path):
    print "Test Log path exists in this filer -- traversing to test log"
    test_base_log_path += "/" + test_name_url
    if os.path.exists(test_base_log_path):
      print test_base_log_path
      return test_base_log_path
    else:
      print "Error while traversing to test logs folder"
      return None
  else:
    print "test base log path traverse failed"
    return None

def execute(cmd):
  """
  Executes command
  """
  pp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
  out, err = pp.communicate()
  return out


def mount_filer(to_path, base_dir_name, drt=None):
  """
  Test name
  """
  exec_path = execute('pwd')
  print "Test Execution Path ->",exec_path
  file_server = "10.14.5.26"
  dir_name = "OSL_filer"
  if drt:
    file_server = "10.4.208.164"
    dir_name = "DRT_filer"
  base_url = '%s:/srv/' % file_server
  print "\n"
  print "Mounting logs from this Filer  ->" , base_url
  base_create_dir  = ('mkdir /tmp/%s' % base_dir_name)
  execute(base_create_dir)
  base_create_dir = to_path+"/"+base_dir_name
  os.chdir(base_create_dir)
  create_dir  = ('mkdir %s' % dir_name)
  execute(create_dir)
  print "  Creating Directory %s " % dir_name
  base_local_point = base_create_dir + "/" + dir_name
  os.chdir(base_local_point)
  curr_pwd = execute('pwd')
  print "  Switching Directory to  ", base_local_point 
  if curr_pwd.strip() == base_local_point.strip():
    print "Local Mount base point -> ",base_local_point 
    mount_cmd = 'sudo mount -o noac -t nfs %s %s' % (base_url, base_local_point)
    try:
      execute(mount_cmd)
    except:
      print "mount failed"
      print " === Resetting path =="
      os.chdir(exec_path.strip())
      return None
    else:
      print " === Resetting path =="
      os.chdir(exec_path.strip())
      return base_local_point
  else:
    print "Error In creating directories"
    print "=============Mount Failed=============="

def umount(path=None):
  """
  performs Umount
  """
  if not None:
    umount = "sudo umount -l %s" % path
    try:
      print " = Un mounting =="
      execute(umount)
    except:
      print "Umount failed"
    else:
      return True

to_path="/tmp"
base_dir_name = 'mounted_logs'
if not os.path.ismount(to_path+"/"+base_dir_name+"/DRT_filer"):
  print "DRT filer Not mounted  -- mounting it now ..!!!"
  drt_mount_point = mount_filer(to_path,base_dir_name, drt=True)
else:
  print "DRT filer already mounted"
if not os.path.ismount(to_path+"/"+base_dir_name+"/OSL_filer"):
  print "OSL filed Not mounted -- mounting it now ..!!!"
  osl_mount_point = mount_filer(to_path,base_dir_name, drt=None)
else:
  print "OSL filer already mounted"

"""
test_log = get_test_log_path(drt_mount_point, osl_mount_point, "5ba11071114cdb9f56f451f5" )
os.chdir(test_log)
print execute("ls")
"""
#umount(path=drt_mount_point) 
#umount(path=osl_mount_point) 