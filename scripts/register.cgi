#!/usr/bin/python

# File:        register.cgi
# Date:        3/28/2019
# Author:      Lloyd Dilley
# Description: register.cgi enables users to create SEGS accounts via a CGI-enabled webserver.
#
# License:     Copyright (c) 2019 SEGS Project (http://www.segs.io/)
#              All rights reserved.
#
#              Redistribution and use in source and binary forms, with or without
#              modification, are permitted provided that the following conditions are met:
#                  * Redistributions of source code must retain the above copyright
#                    notice, this list of conditions and the following disclaimer.
#                  * Redistributions in binary form must reproduce the above copyright
#                    notice, this list of conditions and the following disclaimer in the
#                    documentation and/or other materials provided with the distribution.
#                  * Neither the name of the copyright holders nor the names of its
#                    contributors may be used to endorse or promote products derived
#                    from this software without specific prior written permission.
#
#              THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#              ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#              WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#              DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE
#              FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#              DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#              SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#              CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#              OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#              OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Note: If you are using SELinux, you'll need to set the following to call dbtool directly:
#       setsebool -P httpd_can_network_connect_db 1
#       If you are using the MySQL connector, set the following to allow TCP connections:
#       setsebool -P httpd_can_network_connect=1

# Imports
import cgi, cgitb           # for CGI stuff
import hashlib              # for generating dbtool hash
import re                   # for regex pattern matching
import subprocess           # for running system commands
#import os                  # for running system commands (use subprocess instead!)
import sys                  # for I/O streams and Python version
if sys.version_info[0] < 3:
  from pipes import quote   # for defending against arbitrary user input in Python 2.x
else:
  from shlex import quote   # for defending against arbitrary user input in Python 3.x
import traceback            # for debugging
import imp                  # for dependency checking

# Check if MySQL connector is importable
try:
  imp.find_module("mysql.connector")
  mysql_found = True
  import mysql.connector    # for MariaDB/MySQL connectivity
except ImportError:
  mysql_found = False

#######################
### <CONFIGURABLES> ###
#######################
# Enable debugging to display debug messages to web client
debug_mode = False

# Directory where dbtool resides
dbtool_path = "/apps/segs/bin"

# SHA256 hash of dbtool (ensures the executable has not been tampered with)
dbtool_hash = "551dc96e2d91ac47973ce6edb69054079369c4e80d048d785aea82d98a6723ec"

# SEGS default access level
access_level = 1

# MariaDB/MySQL settings (NOT FULLY IMPLEMENTED -- DO NOT USE!)
use_mysql  = False
mysql_user = "dbuser"
mysql_pass = "secret"
mysql_host = "localhost"
mysql_db   = "segs"
########################
### </CONFIGURABLES> ###
########################

# Enable some debug features if debug_mode is active
if debug_mode:
  cgitb.enable()
  sys.stderr = sys.stdout

# Attempt to convert access_level to a string (default to 1)
try:
  access_level = str(access_level)
except ValueError:
  access_level = "1"

# Handle form data
form = cgi.FieldStorage()
username = form.getvalue('username', "")
password = form.getvalue('password', "")
password2 = form.getvalue('password2', "")

# Limit to alphanumeric characters to defend against malicious injection
# ToDo: Expand allowed characters in password and properly escape/sanitize string.
username_pattern = re.compile("^[A-Za-z0-9]{4,12}$")
password_pattern = re.compile("^[A-Za-z0-9]{6,12}$")

# Get current dbtool hash from filesystem and compare it to ours
def check_hash():
  try:
    with open(dbtool_path + "/dbtool", "rb") as dbtool_file:
      dbtool_binary = dbtool_file.read()
      dbtool_hash2 = hashlib.sha256(dbtool_binary).hexdigest()
      if dbtool_hash == dbtool_hash2:
        return True
  except:
    return False
  return False

# Attempt to create the SEGS account if the form data was valid and return success or failure
def create_account(requested_username, requested_password, access_level):
  try:
    # If user wanted to use MySQL, but the connector was not found, they lied to us. Reset it. :)
    if use_mysql and not mysql_found:
      global use_mysql
      use_mysql = False

    if use_mysql:
      # Connect via MySQL socket
      # ToDo: Implement MySQL functionality
      segs_db = mysql.connector.connect(user = mysql_user, password = mysql_pass, host = mysql_host, database = mysql_db)
      segs_db_cursor = segs_db.cursor()
      segs_db_cursor.execute("SHOW TABLES")
      segs_db.close()
    else:
      # Execute dbtool directly if not using MySQL
      # This requires read and execute permissions outside of the webroot directory. As a result, use pipes.quote()
      # (Python 2.x) or shlex.quote() (Python 3.x) on user input to thwart injection. The username and password
      # passed to create_account() should already be clean from a previous regex check, but make sure anyway...
      dbtool_command = "./dbtool adduser -a {} -l {} -p {}".format(quote(access_level), quote(requested_username), quote(requested_password))

      # Check dbtool hash
      if not check_hash():
        return -9731

      # Use subprocess module if possible as it is more versatile than os
      #os.chdir(dbtool_path)
      #os.system(dbtool_command)

      # Run dbtool, wait for result, and return exit code
      dbtool_proc = subprocess.Popen(dbtool_command, cwd = dbtool_path, shell = True, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
      (dbtool_proc_output, dbtool_proc_err) = dbtool_proc.communicate()
      dbtool_proc_status = dbtool_proc.wait()
      if debug_mode:
        print("Error: " + dbtool_proc_err)
        print("Output: " + dbtool_proc_output)
        print("Exit code: " + str(dbtool_proc_status))
      return dbtool_proc.wait() # return exit code
  except:
    if debug_mode:
      traceback.print_exc()
    return -1

# Handle HTML output and informational messages for web clients
def display_page(info_msg = "", msg_color = "red"):
  print("Content-Type: text/html\r\n\r\n")
  print("<html>")
  print("<head>")
  print("<title>SEGS Community Server - Account Registration</title>")
  print("</head>")
  print("<body>")
  print("<center>")
  print("<img src=\"segs_logo.jpg\">")
  print("<h2>SEGS Community Server - Account Registration</h2>")
  if info_msg != "":
    if msg_color == "green":
      print("<p style=\"color:green\">" + info_msg + "</p>")
    else:
      print("<p style=\"color:red\">" + info_msg + "</p>")
  print("<form name=\"registration\" method=\"POST\" action=\"register.cgi\">")
  print("<table>")
  print("<tr><td align=\"right\">Username:</td>")
  print("<td align=\"left\"><input type=\"text\" name=\"username\" /></td></tr>")
  print("<tr><td align=\"right\">Password:</td>")
  print("<td align=\"left\"><input type=\"password\" name=\"password\" /></td></tr>")
  print("<tr><td align=\"right\">Validate Password:</td>")
  print("<td align=\"left\"><input type=\"password\" name=\"password2\" /></td></tr>")
  print("</table>")
  print("<input type=\"submit\" name=\"submit\" value=\"Register!\" />")
  print("</form>")
  print("</center>")
  print("</body>")
  print("</html>")

# Main -- Display form and handle all possible input cases
if username == "" and password == "" and password2 == "":
  display_page()
elif username == "" and password != "":
  display_page("You must enter a username!")
elif username != "" and password == "":
  display_page("You must enter a password!")
elif username == "" and password == "" and password2 != "":
  display_page("You must enter a username!")
elif password != "" and password2 != "" and password != password2:
  display_page("Passwords do not match!")
elif username != "" and password != "" and password2 == "":
  display_page("You must validate your password!")
elif username != "" and password != "" and password == password2:
  if not username_pattern.match(username):
    display_page("Username must consist of 4 to 12 alphanumeric characters!")
  elif not password_pattern.match(password):
    display_page("Password must consist of 6 to 12 alphanumeric characters!")
  elif username_pattern.match(username) and password_pattern.match(password):
    retcode = create_account(username, password, access_level)
    if retcode == 0:
      display_page("You may now log into the server, hero!", "green")
    elif retcode == 10:
      display_page("Username is taken. Please try another.")
    elif retcode == -9731:
      display_page("Mismatching hash! Please contact an administrator.")
    elif retcode != 0 and retcode != 10 and retcode != -9731:
      display_page("Unable to create account! Please contact an administrator.")
else:
  display_page("Unhandled error occurred! Please contact an administrator.")
