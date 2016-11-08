import sys, six, os, time

dev = "NOTSET"
if "CUDA_VISIBLE_DEVICES" in os.environ:
     dev = os.environ["CUDA_VISIBLE_DEVICES"]

with open("f", "a") as f:
    six.print_(sys.argv[1:], dev, file=f)
#    six.print_(sys.argv[1:], dev)

#time.sleep(numpy.random.uniform()*4)
