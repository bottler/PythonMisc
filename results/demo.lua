results = require 'results'

att  = {a="asdf;",b="c"}
print (att)
results.startRun("",att,"","",{})
for i=1,18 do
   results.step(2,2,21,121)
end
results.addResultAttribute("foo","bat")
