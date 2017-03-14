import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
sql="""alter table attribs rename to foo; 
       create table if not exists ATTRIBS(RUN INT, NAME TEXT, ISRESULT INT, VALUE); 
       insert into attribs select RUN,NAME,ISRESULT,VALUE from foo; 
       drop table foo"""
c.executescript(sql)


    
