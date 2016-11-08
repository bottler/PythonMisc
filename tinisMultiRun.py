#Run another python script on sevaral background threads
#using different GPUs

#This would be the outer script inside a tinis GPU job
#where you want to run a certain script for several combinations
#of that script's arguments. This script runs one instance for
#each of the four GPUs

import subprocess, sys, six, threading,os, time, itertools

pythonCmd = "python2.7" #on tinis, specify this properly
pythonScript = "tinisDummyProgram.py"

arg1s = [2,3,4,5,6]
arg2s = range(3)

arglists = [arg1s, arg2s]

arglists = [map(str,i) for i in arglists]
allargs = [list(i) for i in itertools.product(*arglists)]

nArg=0
def getArgs():
    global nArg
    if nArg>=len(allargs):
        return False
    nArg=nArg+1
    return allargs[nArg-1]


def doThread(threadNumber):
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(threadNumber)
    while 1:
        args = getArgs()
        if args==False:
            return
        subprocess.call([pythonCmd, pythonScript] + args, env=env)

threads = []
for i in range(4):
    threads.append(threading.Thread(target=doThread, args=[i]))
for i in threads:
    i.start()
for i in threads:
    i.join()

