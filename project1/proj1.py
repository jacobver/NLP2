import nltk
from math import log, e, pow
from multiprocessing import Pool
import matplotlib.pyplot as plt

class proj1(object):

    def __init__(self,model=2):
        #enC = self.loadData('corpus_1000.en')
        #nlC = self.loadData('corpus_1000.nl')
        enC = self.loadData('hansards.all.e')
        nlC = self.loadData('hansards.all.f')
        self.model = model
        # append 'NULL' to english sentences
        # and initialize t(f|e) 
        self.tfe = {}
        LMs = []
        for k in range(len(enC)):
            enC[k].append('NULL')
            for f in nlC[k]:
                l = len(enC[k])
                m = len(nlC[k])
                if (l,m) not in LMs:
                    LMs.append((l,m))
                for e in enC[k]:
                    self.tfe[(f,e)] = 1

        # normalize tfe to uniform distribution
        unifP = (float) (1)/len(self.tfe)
        for p in self.tfe:
            self.tfe[p] = unifP

        # set up the data structures 
        cjilms_all = [[(j+1,i+1,l,m) for j in range(l) for i in range(m) ] for (l,m) in LMs]
        self.cjilm = {}
        self.cilm = {}
        for cjilms in cjilms_all:
            for (j,i,l,m) in cjilms:
                self.cjilm[(j,i,l,m)] = 0
                self.cilm[(i,l,m)] = 0

        if self.model==1:
            self.qjilm = self.cjilm
        elif self.model == 2:
            unifQ = (float) (1)/len(self.cjilm)
            self.qjilm = {q:unifQ for q in self.cjilm}
        ltqs = self.IBM(enC,nlC,model)

        print(ltqs)
        #plt.plot(ltqs)
        #plt.show()
        self.maxAligns(loadData('handsards.test.e'),loadData('handsards.test.e'))
    # following Collinls lecture notes p.21 
    def IBM(self, enC, nlC,model,T=5):
        d=1
        lastltq = -1 
        ltqs = []
        it = 0
        while it < 15: #d > 0.01:
            print('iteration: ', it)
            it += 1
            
            self.cef = {(e,f):0 for (f,e) in self.tfe}
            self.ce = {e: 0 for (f,e) in self.tfe}
            self.cjilm = {c:0 for c in self.cjilm}
            self.cilm = {c:0 for c in self.cilm}
        
            print('maximizing...')
            self.maximize((enC,nlC))
            # use 4 cpu's to count
            #with Pool(4) as p:
            #    p.map(self.maximize,[(enC[:60000],nlC[:60000]),(enC[60001:120000],nlC[60001:120000]),(enC[120001:180000],nlC[120001:180000]),(enC[180001:],nlC[180001:])])
        
            print('estimating...')
            self.tfe = {(f,e):(self.cef[e,f]/self.ce[e]) for (f,e) in self.tfe}
            self.qjilm = {(j,i,l,m):(self.cjilm[(j,i,l,m)]/self.cilm[(i,l,m)]) for (j,i,l,m) in self.qjilm}
            
            """
            # determine likelihood
            ltq = self.ltq(enC,nlC)
            ltqs.append(ltq)
            d =  ltq - lastltq
            print('-- d: ',d)
            print('-- ltq: ', ltq)
            lastltq = ltq
            """
        return ltqs
    
    def maximize(self,sents):
        enC,nlC = sents

        # precompute denominators of delta
        tf = {}
        for (f,e) in self.tfe:
            if f in tf:
                tf[f] += self.tfe[(f,e)]
            elif f not in tf:
                tf[f] = self.tfe[(f,e)]

                

        # compute new counts to maximize estimation
        for k in range(len(enC)):
            m = len(nlC[k])
            l = len(enC[k])
            for i in range(m):
                f = nlC[k][i]
                if self.model == 2:
                    denom = 0
                    for J in range(l):
                        denom += self.tfe[(f,enC[k][J])]*self.qjilm[(J+1,i+1,l,m)]
                for j in range(l):
                    e = enC[k][j]
                    if self.model == 1:
                        delta = self.tfe[(f,e)] / tf[f]
                    elif self.model == 2:
                        delta = self.tfe[(f,e)]*self.qjilm[(j+1,i+1,l,m)] / denom
                    self.cef[(e,f)] += delta
                    self.ce[e] += delta
                    self.cjilm[(j+1,i+1,l,m)] += delta
                    self.cilm[(i+1,l,m)] += delta


    """
    Determine LogLikelihood
    """
    
    def ltq(self, enC, nlC):
        pf = 0
        for k in range(len(enC)):
            pf_k = 0 
            l = len(enC[k])
            m = len(nlC[k])
            for i in range(len(nlC[k])):
                pfa_k = 0
                for j in range(len(enC[k])):                
                    if ((j+1, i+1,l,m) in self.qjilm and (nlC[k][i],enC[k][j]) in self.tfe):
                        pfa_k += self.qjilm[j+1,i+1,l,m]*self.tfe[(nlC[k][i],enC[k][j])]
                pf_k += log(pfa_k)
            pf+=pow(e,pf_k)
        return pf

    def maxAligns(self,enC,nlC):
        f = open('resAligns','w')
        for k in range(len(enC)):
            l = len(enC[k])
            m = len(nlC[k])
            for i in range(m):
                cur = 0
                max = 0
                for j in range(l-1): # 'NULL' is at the end
                    cur = self.qjilm[(j+1,i+1,l,m)]*self.tfe[nlC[k][i],enC[k][j]]
                    if cur > max:
                        max = cur
                        align = [j+1,i+1]
                f.write('%04d %d %d \n'%(k+1,align[0],align[1]))
        f.close()
              
    
    def loadData(self, fileloc):
        toker = nltk.tokenize.RegexpTokenizer(r'((?<=[^\w\s])\w(?=[^\w\s])|(\W))+', gaps=True)
        #st = nltk.stem.porter.PorterStemmer()
        
        sents = []
        with open(fileloc) as f:
            for s in f.readlines():
                sents.append([w.lower() for w in toker.tokenize(s)])
                
        return sents


if __name__=="__main__":
    proj1()
