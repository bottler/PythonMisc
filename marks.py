import sqlite3
import os, tabulate, numpy
from six import print_

#Jeremy Reizenstein 2016
#This is a simple module for managing the marks to parts of an assignment
#It relies internally on a single sqlite database

#Each candidate can be awarded marks of either numeric or text types.
#A numeric mark type has an OUT_OF value, and optionally a weighting. If a mark type has no weighting, it is taken to be the same as OUT_OF. weightings are used to calculate the total percentage marks. 
# The vast majority of public functions are just for reporting. Aside from initial table creation, the db is only ever modified by the last few functions in this file. They can be disabled by calling disableMutation
#mark types can be tagged, this facility isn't really used
#There is no string handling in this file - unicode in comes out as unicode. If you have a non-ascii character in a mark, maybe you need to add something like -fno-color-diagnostics in your call to the compiler
#candidates can either be specified by candidate number or a string consisting of the candidate number followed by "d".

file = "marks.sqlite"
if os.environ.has_key("MARKS_FILE"):
    file = os.environ["MARKS_FILE"]

con = sqlite3.connect(file)
if 1:
    c = con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS MARKS (CANDIDATE INT, TYPE TEXT, VALUE, OVERRIDDEN)")
    c.execute("CREATE TABLE IF NOT EXISTS TYPES (NAME TEXT, DESCRIPTION TEXT, NOTES TEXT, OUT_OF REAL, WEIGHTING REAL, IMPORTANCE INT)")
    c.execute("CREATE TABLE IF NOT EXISTS TYPE_TAG (TAG TEXT, MARKTYPE TEXT)")
    con.commit()

def candidateToInt(candidate):
    if type(candidate)==str and candidate[-1]=="d":
        return int(candidate[:-1])
    return int(candidate)

def _getMark(markType, candidate):#candidate must be int
    i = con.execute("select value from marks where overridden is null and candidate = ? and type = ?",(candidate,markType)).fetchall()
    if len(i)==0:
        return None
    if len(i)>1:
        raise RuntimeError("more than one value")
    return i[0][0]
   
def truncate(s, n=10):
    if (str==type(s) or unicode == type(s)) and len(s)>n:
        return s[:n]
    return s

def getMark(markType, candidate):
    assertMarkType(markType)
    return _getMark(markType, candidateToInt(candidate))

def tab(tag=None):
    headers = listMarkTypes() if (tag is None) else listMarksWithTag(tag)   
    rows = listCandidates()
    out = [[r]+[truncate(_getMark(markType, r)) for markType in headers] for r in rows]
    headers = [truncate(i,12) for i in headers]
    print (tabulate.tabulate(out, headers = ["candidate"] + headers))

def checkAllMarksAssigned():
    cs = listCandidates()
    for markType in listMarkTypes():
        for candidate in cs:
            if _getMark(markType,candidate) is None:
                print ("no "+markType+" for "+str(candidate))

def tabNumeric(file = False):
#    total=True
    headers = listNumeric()
    rows = listCandidates()
    out = [[r]+[truncate(_getMark(markType, r)) for markType in headers] + [candidateTotalPercentage_(r)]  for r in rows]
    headers.append("TOTAL")
    tab = tabulate.tabulate(out, headers = ["candidate"] + headers)
    if file:
        with open("numericSummary.txt","w") as f:
            print_(tab,file=f)
    else:
        print (tab)

def listMarkTypes():
    i = con.execute("select name from types ").fetchall()
    return [ii for (ii,) in i]
def listNumeric():
    i = con.execute("select name from types where OUT_OF is not null").fetchall()
    return [ii for (ii,) in i]
def listNonNumeric():
    i = con.execute("select name from types where OUT_OF is null").fetchall()
    return [ii for (ii,) in i]
def listCandidates():
    i = con.execute("select distinct(candidate) from marks where OVERRIDDEN is null order by candidate").fetchall()
    return [ii for (ii,) in i]
def listTags():
    i = con.execute("select distinct(tag) from type_tag order by tag").fetchall()
    return [ii for (ii,) in i]
def listTagsOfMark(marktype):
    i = con.execute("select tag from type_tag where marktype = ? order by tag", (marktype,)).fetchall()
    return [ii for (ii,) in i]
def listMarksWithTag(tag):
    i = con.execute("select marktype from type_tag where tag = ?", (tag,)).fetchall()
    return [ii for (ii,) in i]

def hasMark(candidate, markType):
    assertMarkType(markType)
    return _getMark(markType, candidateToInt(candidate)) is not None
def hasTag(mark, tag):
    return (1,) == con.execute("select count(*) from type_tag where marktype = ? and tag = ?", (mark,tag)).fetchone()

def isMarkType(marktype):
    check = con.execute("SELECT COUNT(*) FROM TYPES WHERE NAME = ?", (marktype,)).fetchone()
    return check == (1,)
def assertMarkType(marktype):
    if not isMarkType(marktype):
        raise RuntimeError(str(marktype) + " is not a type of mark I know of")

def isUsedTag(tag):
    return (0,) != con.execute("select count(*) from type_tag where tag = ?", (tag,)).fetchone()

def tagTable():
    headers = listTags()
    rows = listMarkTypes()
    out = [ [r]+["+" if hasTag(r,t) else " " for t in headers] for r in rows]
    print (tabulate.tabulate(out, headers = [""]+headers))

def m():
    return con.execute("select * from types").fetchall()
def n():
    return con.execute("select * from marks").fetchall()
def t():
    return con.execute("select * from type_tag").fetchall()

#def out_of_total():
#    return con.execute("select sum(OUT_OF) from types").fetchone()[0]
def candidateTotalPercentage_(candidate): #candidate an int
    total = 0.0
    denominator = 0.0
    for markType in listNumeric():
        mark = _getMark(markType,candidate)
        if mark is None:
            print ("no "+markType+" for "+str(candidate))
        out_of,weighting = con.execute("select OUT_OF, WEIGHTING from types where name = ?",(markType,)).fetchone()
        if weighting is None:
            weighting = out_of
        denominator = denominator + weighting
        total = total + float(mark) * float(weighting) / float(out_of)
    return 100*total / denominator

def totalWeighting():
    denominator = 0.0
    for markType in listNumeric():
        out_of,weighting = con.execute("select OUT_OF, WEIGHTING from types where name = ?",(markType,)).fetchone()
        if weighting is None:
            weighting = out_of
        denominator = denominator + weighting
    return denominator

def tableWeightings():
    denominator = 0.0
    a=[]
    for markType in listNumeric():
        out_of,weighting = con.execute("select OUT_OF, WEIGHTING from types where name = ?",(markType,)).fetchone()
        if weighting is None:
            weighting = out_of
        denominator = denominator + weighting
        a.append([markType,out_of,weighting])
    print ("totalWeighting: "+str(denominator))
    for aa in a:
        aa.append(100*aa[-1]/denominator)
    print(tabulate.tabulate(a,headers=("name","out of","weight","percentage")))

def candidateTotalPercentage(candidate, decimalPlaces = 0):
    return round(candidateTotalPercentage_(candidateToInt(candidate)),decimalPlaces)

def distribution():
    a=numpy.round(numpy.sort([candidateTotalPercentage_(c) for c in listCandidates()]))
    print_ (numpy.mean(a), numpy.std(a))
    return a

def printMarks(markType):
    for c in listCandidates():
        print_ (c, _getMark(markType,c))

def writeSummary():
    with open("MarkingSummary.txt","w") as f:
        num = listNumeric()
        outofs=dict()
        def p(x): print_(x, file=f)
        p("Marks ")
        totalWeight=totalWeighting()
        for markType in num:
            out_of,weighting, descr = con.execute("select OUT_OF, WEIGHTING, DESCRIPTION from types where name = ?",(markType,)).fetchone()
            outofs[markType]=out_of
            if descr is None:
                descr = ""
            elif len(descr)>1:
                descr = "("+descr+")"
            if weighting is None:
                weighting = out_of
            percentage = 100.0 * weighting / totalWeight
            print_(markType,descr, "out of", out_of, "  worth "+str(percentage)+"%", file=f)
        for candidate in listCandidates():
            print_("\n",candidate, ": ", round(candidateTotalPercentage_(candidate),1), "%", file=f, sep="")
            for markType in listMarkTypes():
                if markType in num:
                    print_(markType,": ",_getMark(markType,candidate),"/", outofs[markType],file=f,sep="")
                else:
                    res = _getMark(markType,candidate)
                    if(len(unicode(res))>1):
                        
                        p(markType)
                        p(res.encode("iso-8859-1"))
        
#Mutation functions are below here
mutationEnabled = True

def disableMutation():
    global mutationEnabled
    mutationEnabled=False

def startMutation():
    if not mutationEnabled:
        raise RuntimeError("no mutation allowed")

def newMark(name, description, outOf = None): #supply outOf if the mark is to be a numeric value
    startMutation()
    if isMarkType(name):
        raise RuntimeError(str(name) + " is a type of mark I already know of")
    c=con.cursor()
    c.execute("INSERT INTO TYPES (NAME, DESCRIPTION, NOTES, OUT_OF, WEIGHTING, IMPORTANCE) VALUES (?,?,'',?,NULL,1)",(name,description,outOf))
    con.commit()

def setWeighting(markType, weighting):
    startMutation()
    if markType not in listNumeric():
        raise RuntimeError(str(markType) + " is not a type of numeric mark I already know of")
    if type(weighting) not in (type(None), float,int):
        raise RuntimeError("not a good weight type")
    c.execute("update types set WEIGHTING=? WHERE NAME = ?",(weighting,markType))
    con.commit()

def tagMark(marktype, tag, remove = False):
    startMutation()
    assertMarkType(marktype)
    if (not remove) and hasTag(marktype, tag):
        raise RuntimeError(str(marktype) + " is already tagged with "+tag)
    if remove and not hasTag(marktype, tag):
        raise RuntimeError(str(marktype) + " is not already tagged with "+tag)
    if remove:
        con.execute("delete from type_tag where marktype = ? and tag = ?", (marktype, tag))
    else:
        con.execute("insert into type_tag (marktype, tag) values (?,?)", (marktype, tag))
    con.commit()

def _removeMark(candidate, marktype, c):
    c.execute ("UPDATE MARKS SET OVERRIDDEN = DATETIME('NOW') WHERE CANDIDATE = ? AND TYPE = ? and OVERRIDDEN is NULL", (candidate, marktype))

def removeMark(candidate, marktype):
    startMutation()
    c = con.cursor()
    assertMarkType(marktype)
    if not hasMark(candidate, markType):
        raise RuntimeError(str(marktype) + " has not been given to "+candidate)
    _removeMark(candidateToInt(candidate), marktype, c)
    con.commit()

def assignMark(candidate, marktype, value, force = False):
    startMutation()
    candidate = candidateToInt(candidate)
    c = con.cursor()
    assertMarkType(marktype)
    isNumeric = c.execute("SELECT OUT_OF is not NULL from TYPES where name = ?", (marktype,)).fetchone()
    isNumeric = isNumeric != (0,)
    if isNumeric and type(value) == str:
        raise RuntimeError(str(marktype) + " is a numeric mark. It cannot be given this value.")
    #perhaps should check numeric marks are in range.
    if _getMark(marktype,candidate) is not None:
        if force:
            _removeMark(candidate, marktype, c)
        else:
            raise RuntimeError(str(marktype) + " has already been assigned to "+str(candidate))
    c.execute("INSERT INTO MARKS (CANDIDATE, TYPE, VALUE, OVERRIDDEN) VALUES (?,?,?,NULL)",(candidate,marktype,value))
    con.commit()

