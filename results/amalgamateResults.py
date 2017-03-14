import sys
import os
import sqlite3
#Creates a file resultsAmalgam.sqlite which is an amalgamation of all the results files named on the command line
#at the moment, assume they are are all new format
filename = "resultsAmalgam.sqlite"
if os.path.isfile(filename):
    raise RuntimeError("file "+filename+" already exists")

con = sqlite3.connect(filename)
c=con.cursor()

if not os.path.isfile(sys.argv[1]):
    raise RuntimeError("no file "+sys.argv[1])
c.execute("attach ? as o",(sys.argv[1],))
runColList="(COUNT INTEGER PRIMARY KEY, TIME TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, CONTINUATION TEXT, ARCHITECTURE TEXT, SOLVER TEXT, CODE TEXT)"
setup=["create table if not exists RUNS"+runColList,#these default keys start at 1
       "create table if not exists STEPS(STEP INTEGER PRIMARY KEY, RUN int, OBJECTIVE real, TRAINACC real, TESTOBJECTIVE real, TESTACC REAL )",
       "create table if not exists TIMES(RUN INT, TIME real)", # stores the time of the tenth step of each run, allowing speed to be measured
       "create table if not exists ATTRIBS(RUN INT, NAME TEXT, ISRESULT INT, VALUE)"
       ]
for s in setup:
    c.execute(s)

print (sys.argv[1])
c.execute("insert into RUNS SELECT * FROM o.RUNS") #Thus proving the DB is new format
nrun=c.lastrowid
c.execute("insert into STEPS SELECT * FROM o.STEPS")
c.execute("insert into TIMES SELECT * FROM o.TIMES")
c.execute("insert into ATTRIBS SELECT * FROM o.ATTRIBS")
c.execute("detach o")

for t in sys.argv[2:]:
    if not os.path.isfile(t):
        raise RuntimeError("no file "+t)
    c.execute("attach ? as o",(t,))
    if c.execute("select sql like '%LAYERTYPE%' from sqlite_master where tbl_name='RUNS'").fetchone()[0]:
        raise RuntimeError(t + " has old columns, can't deal with it here")
    print (t)
    c.execute("insert into RUNS SELECT COUNT+?,TIME,CONTINUATION,ARCHITECTURE,SOLVER,CODE FROM o.RUNS",(nrun,))
    next_nrun=c.lastrowid
    c.execute("insert into STEPS(RUN,OBJECTIVE,TRAINACC,TESTOBJECTIVE,TESTACC) SELECT RUN+?,OBJECTIVE,TRAINACC,TESTOBJECTIVE,TESTACC FROM O.STEPS",(nrun,))
    c.execute("insert into TIMES select RUN+?, TIME FROM O.TIMES",(nrun,))
    c.execute("insert into ATTRIBS SELECT RUN+?, NAME, ISRESULT, VALUE FROM O.ATTRIBS",(nrun,))
    nrun=next_nrun
    c.execute("detach o")

