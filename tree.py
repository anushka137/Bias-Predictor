# project: p2
# submitter: achandrashe4
# partner: none
# hours: 12

from zipfile import ZipFile
from io import TextIOWrapper
import json, csv

class ZippedCSVReader:
    def __init__(self, filename):
        self.filename = filename
        with ZipFile(self.filename) as zf:
            self.paths = zf.namelist()
        
    def load_json(self, json_file):
        with ZipFile(self.filename) as zf:
            with zf.open(json_file, "r") as f:
                d = json.load(f)
        return d
    
    def rows(self, csv_file = None):
        if csv_file == None:
            big_list = []
            with ZipFile(self.filename) as zf:
                for info in zf.infolist():
                    with zf.open(info, "r") as f:
                        tio = TextIOWrapper(f)
                        reader = csv.DictReader(tio)
                        for row in reader:
                            row = dict(row)
                            big_list.append(row)
            return big_list
        else:
            specific_list = []
            with ZipFile(self.filename) as zf:
                with zf.open(csv_file, "r") as f:
                    tio = TextIOWrapper(f)
                    reader = csv.DictReader(tio)
                    for row in reader:
                        row = dict(row)
                        specific_list.append(row)
            return specific_list
        
class Loan:
    def __init__(self, amount, purpose, race, income, decision):
        self.amount = amount
        self.purpose = purpose
        self.race = race
        self.income = income
        self.decision = decision
        
    def __repr__(self):
        return f"Loan({repr(self.amount)}, {repr(self.purpose)}, {repr(self.race)}, {repr(self.income)}, {repr(self.decision)})"

    def __getitem__(self, lookup):
        if hasattr(self, lookup):
            return getattr(self, lookup)
        
        values = [self.amount, self.purpose, self.race, self.income, self.decision]
        
        if lookup in values:
            return 1
        else:
            return 0

class Bank:
    def __init__(self, name, reader):
        self.name = name
        self.reader = reader
        
    def loans(self):
        list_of_dicts = ZippedCSVReader.rows(self.reader)
        loans = []
        for d in list_of_dicts:
            if self.name is None:
                ln = self.build_loan(d)
                loans.append(ln)
            elif d["agency_abbr"] == self.name:
                ln = self.build_loan(d)
                loans.append(ln)

        return loans

    def build_loan(self, d):
        if d["action_taken"] == "1":
            d["action_taken"] = "approve"
        else:
            d["action_taken"] = "deny"
        if d["loan_amount_000s"] == "":
            loan_amount = 0
        else:
            loan_amount = int(d["loan_amount_000s"])
        if d["applicant_income_000s"] == "":
            income_amount = 0
        else:
            income_amount = int(d["applicant_income_000s"])
        
        return Loan(loan_amount,
                d["loan_purpose_name"],
                d["applicant_race_name_1"],
                income_amount,
                d["action_taken"])

def get_bank_names(reader):
    bank_names = set()
    csv_list = reader.rows()
    for item in csv_list:
        bank_names.add(item["agency_abbr"])
    return list(sorted(bank_names))

class SimplePredictor():
    def __init__(self):
        self.num_approved = 0
        self.num_denied = 0
    
    def predict(self, loan):
        if loan["purpose"] == "Refinancing":
            self.num_approved += 1
            return True
        self.num_denied += 1
        return False
    
    def get_approved(self):
        return self.num_approved
    
    def get_denied(self):
        return self.num_denied
    
class DTree(SimplePredictor):
    def __init__(self, nodes):
        super().__init__() 

        # a dict with keys: field, threshold, left, right
        # left and right, if set, refer to similar dicts
        self.root = nodes
        
    def dump(self, node=None, indent=0):
        if node == None:
            node = self.root
            
        if node["field"] == "class":
            line = "class=" + str(node["threshold"])
        else:
            line = node["field"] + " <= " + str(node["threshold"])
        print("  "*indent + line)
        if node["left"]:
            self.dump(node["left"], indent+1)
        if node["right"]:
            self.dump(node["right"], indent+1)
            
    def node_count(self, node = None):   
        if node == None:
            node = self.root
        count = 1
        
        if node["left"]:
            count += self.node_count(node["left"])
            
        if node["right"]:
            count += self.node_count(node["right"])
        
        return count

    def predict(self, loan, node = None):
        if node == None:
            node = self.root
            
        if node["field"] == "class": 
            if node["threshold"] == 0:
                self.num_denied += 1
                return False
            else:
                self.num_approved += 1
                return True
        
        if loan[node["field"]] <= node["threshold"]:
            return self.predict(loan, node["left"])
        else:
            return self.predict(loan, node["right"])

        
def bias_test(bank, predictor, race_override):
        diff = 0
        total = len(bank.loans())
        
        for loan in bank.loans():
            result1 = predictor.predict(loan)
            loan.race = race_override
            result2 = predictor.predict(loan)
            
            if(result1 != result2):
                diff += 1
                
        return diff / total
      