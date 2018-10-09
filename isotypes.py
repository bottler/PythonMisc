import numpy as np
from sympy.combinatorics.partitions import IntegerPartition
from sympy.combinatorics.permutations import Permutation
from sympy.combinatorics.generators import symmetric
from sympy.utilities.iterables import partitions, permutations
import sys, itertools, functools, operator, math
np.set_printoptions(suppress=True)

#This file attempts to provide a function "project" to give an isotypical component of a tensor.
#The rest of the file is just part of its implementation or testing

#(4,3,1) -> [[0,1,2,3],[4,5,6],[7]]
def triangleOfNumbers(partition, forceList=False):
    a=0
    o=[]
    for i in partition:
        x=a+np.arange(i)
        if forceList:
            x=list(x)
        o.append(x)
        a += i
    return o

def isStandard(tableau):
    for row in tableau:
        if len(row)>1 and any(row[j-1]>row[j] for j in range(1,len(row))):
            return False
    for ncol in range(len(tableau[0])):
        for nrow in range(1,len(tableau)):
            if len(tableau[nrow])<ncol+1:
                break
            if tableau[nrow][ncol]<tableau[nrow-1][ncol]:
                return False
    return True

def conjugatePartition(partition):
    return [sum(j>i for j in partition) for i in range(partition[0])]
        
#output begins at 0
#This is an inefficient but obvious way to enumerate standard Young tableaux.
def enumerate_standard_Young_tableax(partition):
    n=sum(partition)
    orig = triangleOfNumbers(partition)
    o=[]
    for permutation in symmetric(n):
        new = [[permutation(i) for i in j] for j in orig]
        #new = [permutation(j) for j in orig]
        if isStandard(new):
            #yield new
            o.append(new)
    return o
def enumerate_Young_tableax_and_count_standard(partition):
    n=sum(partition)
    orig = triangleOfNumbers(partition)
    o=[]
    count=0
    for permutation in symmetric(n):
        new = [[permutation(i) for i in j] for j in orig]
        #new = [permutation(j) for j in orig]
        if isStandard(new):
            count += 1
        o.append(new)
    return o,count

def getRowColumnPermutations(partition):
    each_row_permutation = [list(symmetric(i)) for i in partition]
    each_col_permutation = [list(symmetric(i)) for i in conjugatePartition(partition)]
    return each_row_permutation,each_col_permutation
    
#If tableau is a standard young tableau (which this function does
#not check) then
#return the corresponding young symmetrizer (a signed list of permutations)
#as a list of tuples
#This function spends a lot of its time in symmetric, which can be saved
#by supplying the optional argument - this must be what this function would calculate for itself
def unchecked_young_symmetrizer(tableau,
                                each_row_col_permutation=None):
    if each_row_col_permutation is not None:
        each_row_permutation,each_column_permutation = each_row_col_permutation
    else:
        x=getRowColumnPermutations([len(i) for i in tableau])
        each_row_permutation,each_column_permutation = x
    row_permutations = []
    col_permutations = []
    for i in itertools.product(*each_row_permutation):
        row_transformed_tableau=[j(tableau[n]) for  n,j in enumerate(i)]
        mapping = {i:j for I,J in zip(row_transformed_tableau,tableau) for i,j in zip(I,J)}
        row_permutation=Permutation([mapping[i] for i in range(len(mapping))])
        row_permutations.append(row_permutation)
    for i in itertools.product(*each_column_permutation):
        column_transformed_tableau=[[jj for jj in j] for j in tableau]
        for irow in range(len(tableau)):
            for icol in range(len(tableau[irow])):
                column_transformed_tableau[irow][icol]=tableau[i[icol](irow)][icol]
        mapping = {i:j for I,J in zip(column_transformed_tableau,tableau) for i,j in zip(I,J)}
        col_permutation=Permutation([mapping[i] for i in range(len(mapping))])
        col_permutations.append(col_permutation)
    return [(c.signature(),r*c) for r in row_permutations for c in col_permutations]

def unchecked_project_to_tableau(tensor,tableau,each_row_col_permutation=None):
    total=np.zeros_like(tensor, dtype="float64")
    n=tensor.ndim
    for sign,permutation in unchecked_young_symmetrizer(tableau,each_row_col_permutation):
        sequence = permutation(range(n))
        #Inverting the permutation here and reversing the r*c in unchecked_young_symmetrizer cancels out
        #sequence = (~permutation)(range(n))
        
        #total += sign*np.transpose(tensor,sequence)
        if sign>0:
            total += np.transpose(tensor,sequence)
        else:
            total -= np.transpose(tensor,sequence)
    return total
    

#tableaux could be optionally provided to this function to save time.
#this is following Proposition 9.3.12 (p401) of Goodman & Wallach, "Representations and Invariants of the Classical Groups"
def project(tensor, partition):
    """the isotypical component of tensor corresponding to the partition"""
    d=tensor.shape[0]
    n=tensor.ndim
    ncols=partition[0]
    nrows=len(partition)
    assert all(i==d for i in tensor.shape)
    assert n==sum(partition)
    assert all(i>0 for i in partition)
    for i in range(1,len(partition)):
        assert(partition[i]<=partition[i-1])
    total=np.zeros_like(tensor, dtype="float64")
    each_row_col_permutation = getRowColumnPermutations(partition)
    tableaux,countStd=enumerate_Young_tableax_and_count_standard(partition)
    for tableau in tableaux:
        total += unchecked_project_to_tableau(tensor,tableau,each_row_col_permutation)
    factor=((countStd+0.0)/math.factorial(n))
    return total*factor*factor

def testIsotypePartition(tensor):
    """Test that the components of tensor add up to tensor, 
    that projecting them again the same way leaves them unchanged,
    and that projecting them differently leaves them zero"""
    #print("---")
    total = np.zeros_like(tensor, dtype="float64")
    for pp in partitions(tensor.ndim):
        p = IntegerPartition(pp).partition
        t=project(tensor, p)
        #print (p)
        #print(";")
        #print(t)
        #print(t-project(t,p))
        #print(project(t,p))
        assert np.allclose(t,project(t,p))
        #print(tensor,total,t)
        total += t
        for qq in partitions(tensor.ndim):
            q=IntegerPartition(qq).partition
            if q!=p:
                #print(p,q)
                #print(project(t,q))
                assert np.allclose(0,project(t,q))
    #print(".")
    #print(tensor)
    #print(total)
    assert np.allclose(tensor,total)
    print("test ok")


def randomTensor(d,m):
    return np.random.rand(*([d]*m))
def tensorWithSingleOne(index,min_d=None):
    """the tensor full of zeros with a one at location index"""
    m=len(index)
    d=max(index)+1
    if min_d is not None and min_d>d:
        d=min_d
    o=np.zeros([d]*m)
    o.__setitem__(tuple(index),1)
    return o
def testAllSingleOnes(d,m):
    for i in itertools.product(range(d),repeat=m):
        tensor = tensorWithSingleOne(i,min_d=d)
        try:
            testIsotypePartition(tensor)
        except AssertionError:
            print("{} failed".format(i))

if __name__=="__main__":
            
    if 0:
        import young_symmetrization
        from young_symmetrization import young_symmetrizer, young
        for i in unchecked_young_symmetrizer([[0,1,2],[3,4]]):
            print (i)
        for i in young_symmetrizer( young.Young( [[1,2,3],[4,5]] ) ).data.items():
            print(i)
        sys.exit()
    
    #testAllSingleOnes(2,5)

    if 0:
        #a=np.random.rand(2,2)
        a=np.array([[2,3],[4,5]])
        a_anti=project(a,[1,1])
        #print("***")
        a_sym=project(a,[2])
        print(a)
        print(a_anti)
        print(a_sym)
        testIsotypePartition(a)



    if 1:
        testIsotypePartition(np.random.rand(4,4))
        #print(project(np.random.rand(3,3,3),[1,1,1]))
        testIsotypePartition(np.random.rand(3,3,3))
        testIsotypePartition(np.random.rand(7,7,7,7))
        testIsotypePartition(np.random.rand(5,5,5,5,5))
