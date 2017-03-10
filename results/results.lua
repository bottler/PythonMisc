require "lsqlite3"
require 'sys'

local results = {}

filename = os.getenv("JR_RESULTSFILE") or "results.sqlite"
con = sqlite3.open(filename)
filecontents = ""
oldColumns=False

function append_file_to_filecontents_string(f)
   local ff = io.open(f,"r")
   local content = ff:read("*all")
   ff:close()
   filecontents = filecontents .. f .."\n"..content
end

function check(x)
   if x~=sqlite3.OK then
      error(con:errmsg())
   end
end

--if sql is a statement which doesn't return results,
--resultless(sql, param1, param2) executes it with the given parameters
function resultless(st, ...)
   local s = con:prepare(st)
   if not s then
      error(con:errmsg())
   end
   s:bind_values(...)
   local res = s:step()
   if res==sqlite3.ROW then
      error("resultless: the query returned something")
   end
   if res~=sqlite3.DONE then
      error(con:errmsg())
   end
   s:finalize()
end
function singleValuedQuery(st, ...)
   local s = con:prepare(st)
   if not s then
      error(con:errmsg())
   end
   s:bind_values(...)
   local res = s:step()
   if res==sqlite3.DONE then
      error("the query returned nothing")
   end
   if res~=sqlite3.ROW then
      error(con:errmsg())
   end
   if s:columns()~= 1 then
      error("the query returned multiple columns")
   end
   local o = s:get_value(0)
   res=s:step()
   if res~=sqlite3.DONE then
      error("perhaps the query returned more than one row")
   end
   s:finalize()
   return o
end

function results.startRun(continuation, attribs, architecture, solver, callerFilePath)
   if "table" == type(callerFilePath) then
      for i,name in ipairs(callerFilePath) do
         append_file_to_filecontents_string(name)
      end
   else
      append_file_to_filecontents_string(callerFilePath)
   end
   local runColList="(COUNT INTEGER PRIMARY KEY, TIME TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, REPN TEXT, REPNLENGTH INT, CONTINUATION TEXT, BATCHTR INT, BATCHTE INT, LAYERTYPE TEXT, LAYERS INT, WIDTH INT, ARCHITECTURE TEXT, SOLVER TEXT, CODE TEXT)"
   if not oldColumns then
      runColList="(COUNT INTEGER PRIMARY KEY, TIME TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, CONTINUATION TEXT, ARCHITECTURE TEXT, SOLVER TEXT, CODE TEXT)"
   end
   local setup="create table if not exists RUNS" .. runColList .. [[;
      create table if not exists STEPS(STEP INTEGER PRIMARY KEY, RUN int, OBJECTIVE real, TRAINACC real, TESTOBJECTIVE real, TESTACC REAL );
      create table if not exists TIMES(RUN INT, TIME real);
      create table if not exists ATTRIBS(RUN INT, NAME TEXT, ISRESULT INT, VALUE TEXT)
   ]]
   check(con:exec(setup))
   local infoquery = "insert into RUNS (CONTINUATION, ARCHITECTURE, SOLVER, CODE) VALUES (?,?,?,?)"
   local info = {continuation, architecture, solver, filecontents}
   local attribquery = "insert into ATTRIBS(RUN, NAME, ISRESULT, VALUE) VALUES (?,?,0,?)"
   resultless(infoquery,unpack(info))
   nrun = con:last_insert_rowid()
   for k,v in pairs(attribs) do
      resultless(attribquery,nrun,k,v)
   end
   nsteps = 0
   filecontents = nil
end

function results.step(obj,train,objte,test)
   nsteps = 1+nsteps
   resultless("insert into steps values (NULL, ?, ?, ?, ?, ?)", nrun,obj,train,objte, test)
   if nsteps == 1 then
      sys.tic()
   end
   if nsteps == 11 then
      resultless("insert into TIMES VALUES (?,?)", nrun, sys.toc())
   end
end

function results.addResultAttribute(name, value)
   if 1 then
      count = singleValuedQuery("select count(*) from ATTRIBS where run = ? and name = ?",nrun,name)
      if count > 0 then
         error("attribute already set:" .. name)
      end
   end
   resultless("insert into ATTRIBS(RUN, NAME, ISRESULT, VALUE) VALUES (?,?,1,?)",nrun,name,value)
end

return results
