require "lsqlite3"
require 'sys'

local results = {}

filename = os.getenv("JR_RESULTSFILE") or "results.sqlite"
con = sqlite3.open(filename)
filecontents = ""

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
   assert(s)
   s:bind_values(...)
   local res = s:step()
   if res~=sqlite3.DONE then
      error(con:errmsg())
   end
   s:finalize()
end

function results.startRun(repnname, repnlength, continuation, batchTr, batchTe, layertype, layers, width, architecture, solver, callerFilePath)
   if "table" == type(callerFilePath) then
      for i,name in ipairs(callerFilePath) do
         append_file_to_filecontents_string(name)
      end
   else
      append_file_to_filecontents_string(callerFilePath)
   end
   local setup=[[create table if not exists RUNS(COUNT INTEGER PRIMARY KEY, TIME TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, REPN TEXT, REPNLENGTH INT, CONTINUATION TEXT, BATCHTR INT, BATCHTE INT, LAYERTYPE TEXT, LAYERS INT, WIDTH INT, ARCHITECTURE TEXT, SOLVER TEXT, CODE TEXT)   ;
   create table if not exists STEPS(STEP INTEGER PRIMARY KEY, RUN int, OBJECTIVE real, TRAINACC real, TESTOBJECTIVE real, TESTACC REAL );
   create table if not exists TIMES(RUN INT, TIME real)
   ]]
   check(con:exec(setup))
   local infoquery = "insert into RUNS (REPN, REPNLENGTH, CONTINUATION, BATCHTR, BATCHTE, LAYERTYPE, LAYERS, WIDTH, ARCHITECTURE, SOLVER, CODE) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
   local info = {repnname, repnlength, continuation, batchTr, batchTe, layertype, layers, width, architecture, solver, filecontents}
   resultless(infoquery,unpack(info))
   nrun = con:last_insert_rowid()
   sys.tic()
   nsteps = 0
   filecontents = nil
end

function results.step(obj,train,objte,test)
   nsteps = 1+nsteps
   resultless("insert into steps values (NULL, ?, ?, ?, ?, ?)", nrun,obj,train,objte, test)
   if nsteps == 10 then
      resultless("insert into TIMES VALUES (?,?)", nrun, sys.toc())
   end
end

return results
