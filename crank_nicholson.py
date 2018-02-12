from scipy.sparse import diags
import scipy.linalg
import numpy as np, sys
#np.set_printoptions(precision=3)

#solve
#du/dt = D d2u/dx^2 + a du/dx + f(u)
#forward in time for a length of time T e.g. [0,T]
#on an interval of length L e.g. [0,L]
#formulae of http://georg.io/2013/12/Crank_Nicolson_Convection_Diffusion

#Can easily modify the code to make f be a function of x or t too,
#but would then actually care about their values.

#f should be a vectorized function or just return a constant
#u is the initial condition u(0,x)

#BC order is the derivative of u which is assumed 0 at the edge
#0 means Dirichlet (so you just assume there's a fixed 0 beyond
#      the edge, so the edge equation is just like the bulk
#      -i.e. the diagonals are constant
#1 means Neumann (like georg.io)
#2 means second deriv is 0
#      so the imaginary point is like u[-1]-u[0]=u[0]-u[1] or u[-1]=2*u[0]-u[1]

#Or: -1 means Dirichlet where the edges are not fixed at 0 but
#at whatever the corresponding edge value in the IC is.

def crank_nicholson(u, L, T, n_timesteps, D, a = 0,
                   f = lambda u: 0, leftBCOrder=2, rightBCOrder=2):
    nx = np.shape(u)[0]
    dx = L/(nx-1.)
    dt = T/(n_timesteps+0.0)
    sigma = D*dt/(2.*dx*dx)
    rho = a*dt/(4.*dx)

    A=np.zeros((3,nx))
    A[0,:]=-(sigma+rho)
    A[2,:]=rho-sigma
    A[1,:]=1+2*sigma
    A[1,0]=(1,1+2*sigma,1+sigma+rho,1+2*rho)[leftBCOrder+1]
    A[1,-1]=(1,1+2*sigma,1+sigma-rho,1-2*rho)[rightBCOrder+1]
    A[0,1]=(0,-(sigma+rho),-(sigma+rho),-2*rho)[leftBCOrder+1]
    A[2,-2]=(0,rho-sigma,rho-sigma,2*rho)[rightBCOrder+1]
    if 0:
        dense_A=diags([A[2,:-1],A[1,:],A[0,1:]],[-1,0,1]).toarray()
        print (dense_A)

    B_dia=(1-2*sigma)*np.ones(nx)
    B_top=(sigma+rho)*np.ones(nx-1)
    B_bot=(sigma-rho)*np.ones(nx-1)
    B_dia[0] =(1,1-2*sigma,1-sigma-rho,1-2*rho)[leftBCOrder+1]
    B_dia[-1]=(1,1-2*sigma,1-sigma+rho,1+2*rho)[rightBCOrder+1]
    B_top[0]=(0,sigma+rho,sigma+rho,2*rho)[leftBCOrder+1]
    B_bot[-1]=(0,sigma-rho,sigma-rho,-2*rho)[rightBCOrder+1]
    #B=diags([sigma-rho,B_dia,sigma+rho],[-1,0,1],shape=(nx,nx))
    B=diags([B_bot,B_dia,B_top],[-1,0,1],shape=(nx,nx))
    #print(B.toarray())

    for idx in range(n_timesteps):
        rhs=B.dot(u)+dt*f(u)
        u = scipy.linalg.solve_banded((1,1),A,rhs)
    return u

if __name__=="__main__":
    n=100
    u=np.concatenate([np.zeros(n//2),np.ones(n//2)])
    u=np.arange(n)/10.
    u=u[::-1]
    #u=np.ones(n)
    u_source=(np.arange(n)-n//2)/(n/2.)
    u=np.abs(u_source)
    #u=[min(i,0.3) for i in u]
    D=0.01
    nt=100
    L=1
    T=10
    out=crank_nicholson(u,L,T, nt,D,0,lambda u:0)
    out2=crank_nicholson(u,L,T, nt,D,-0.003)
    #print(out2-out)
    from matplotlib import pyplot as plt
    x=list(range(n))
    plt.plot(x,out,x,out2)
    plt.show()
