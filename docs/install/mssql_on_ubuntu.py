http://www.pauldeden.com/2008/12/how-to-setup-pyodbc-to-connect-to-mssql.html

How to setup pyodbc to connect to MSSQL from ubuntu linux
Pyodbc is a great python sql db 2.0 interface to odbc. It is a mature and well written library.

It's also a little hard to setup on linux due to all the pieces involved, but never fear, here are the steps on Ubuntu 8.04. The following will show you how to setup the dsn-less setup. This way you don't have to setup DSNs for each connection. Thanks Guillermo for the tip.

sudo aptitude install unixodbc unixodbc-dev freetds-bin freetds-dev tdsodbc python-dev

Change /etc/odbcinst.ini to

[FreeTDS]
Description = TDS driver (Sybase/MS SQL)
Driver = /usr/lib/odbc/libtdsodbc.so
Setup = /usr/lib/odbc/libtdsS.so
CPTimeout =
CPReuse =

Now unixodbc and freetds are setup.

On to pyodbc itself.

Download the current version of pyodbc

Unzip the file.

Do a

sudo python setup.py install

All done.

Test it with

python
>>> import pyodbc
>>> conn = pyodbc.connect("DRIVER={FreeTDS};SERVER=dns_or_ip_of_server;UID=username;PWD=password;DATABASE=database_name")

No errors and it is installed and working!

More details here and here. 


/etc/odbcinst.ini, on 32 bit
-------------------------------------------------------------------
[SQL Server]
Description = FreeTDS
Driver = /usr/lib/i386-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/i386-linux-gnu/odbc/libtdsS.so
CPTimeout =
CPReuse =
#UnicodeTranslationOption = utf32
-------------------------------------------------------------------


/etc/odbcinst.ini, on 64 bit
-------------------------------------------------------------------
[SQL Server]
Description = FreeTDS
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
CPTimeout =
CPReuse =
#UnicodeTranslationOption = utf32
-------------------------------------------------------------------


/etc/freetds/freetds.conf 
-------------------------------------------------------------------
#   $Id: mssql_on_ubuntu.py,v 1.2 2015/03/19 17:35:43 oleg Exp $
#
# This file is installed by FreeTDS if no file by the same 
# name is found in the installation directory.  
#
# For information about the layout of this file and its settings, 
# see the freetds.conf manpage "man freetds.conf".  

# Global settings are overridden by those in a database
# server specific section
[global]
        # TDS protocol version
	tds version = 8.0

	# Whether to write a TDSDUMP file for diagnostic purposes
	# (setting this to /tmp is insecure on a multi-user system)
;	dump file = /tmp/freetds.log
;	debug flags = 0xffff

	# Command and connection timeouts
;	timeout = 10
;	connect timeout = 10
	
	# If you get out-of-memory errors, it may mean that your client
	# is trying to allocate a huge buffer for a TEXT field.  
	# Try setting 'text size' to a more reasonable limit 
	text size = 64512

# A typical Sybase server
;[egServer50]
;	host = symachine.domain.com
;	port = 5000
;	tds version = 5.0

# A typical Microsoft server
;[egServer70]
;	host = ntmachine.domain.com
;	port = 1433
;	tds version = 7.0

[192.168.2.5]
	host = 192.168.2.5
	port = 1433
	client charset = CP1251
-------------------------------------------------------------------

Error: ('HY000', 'The driver did not supply an error!') 

QUERY MUST BE IN cp1251 to avoid this error
