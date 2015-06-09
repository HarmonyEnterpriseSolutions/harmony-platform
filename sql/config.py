pg_bin   = ''
username = "postgres"
host     = "localhost"
port     = "5432"
psql     = 'psql'
pg_dump  = 'pg_dump'

import os
if not pg_bin:
	pro = os.getenv('ProgramFiles')
	if pro:
		pg_bin = os.path.join(pro, 'PostgreSql', '8.4', 'bin')
		if not os.path.exists(pg_bin):
			pg_bin = os.path.join(pro, 'PostgreSql', '8.3', 'bin')
			if not os.path.exists(pg_bin):
				pg_bin = os.path.join(pro, 'PostgreSql', '8.2', 'bin')
	else:
		pg_bin = '/usr/bin'

if pg_bin:
	psql     = os.path.join(pg_bin, 'psql')
	pg_dump  = os.path.join(pg_bin, 'pg_dump')
