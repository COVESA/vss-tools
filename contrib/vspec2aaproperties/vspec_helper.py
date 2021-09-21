from anytree import Resolver

class VSpecHelper:
    def __init__(self,tree):
        self.tree=tree
        self.r=Resolver("name")
    def __getitem__(self,item):
        return self.r.get(self.tree,f'/{item.replace(".","/")}')

