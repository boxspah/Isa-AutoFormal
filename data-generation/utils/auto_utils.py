
import re
import copy
import nltk
from utils.utils import timeout
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize 

# from check import checker
header_words = ['To', 'Now', 'However', 'Therefore', 'Hence', 'Thus', 'So', 'Again', 'Let', 'Let\'s', 'We', 'From', 'According', 'By', 'To', 'When', 'Similarly', \
                'Apply', 'Applying', 'Substitute', 'Substituting', 'Simplify', 'Simplifying', 'Use', 'Using', 'Solve', 'Solving', 'Expand', 'Expanding', \
                'Factor', 'Factoring', 'Rearrange', 'Rearranging', 'Combine', 'Combining', 'Start', 'Starting', \
                'Add', 'Adding', 'Divide', 'Dividing', 'Multiply', 'Multiplying', 'Subtract', 'Subtracting', ]
tail_words = [':', ': ', ',', ', ']

# the input is natural language solution
def parse_answer(sol):
    pattern = r"\\boxed{((?:[^{}]|{[^{}]*})*)}"   
    results = re.findall(pattern, ('\n'.join(sol)))
    if len(results) > 0:
        return results[-1]
    else:
        return str(0)

# the input is natural language solution
def normalize_answer(answer):
    answer = '\n'.join(sent_tokenize(answer))
    answer = answer.replace('{*', '{').replace('*}', '}')
    sentences = [a for a in answer.split('\n') if a != '']
    result = []  
    # define some rule for line break
    for sentence in sentences: 
        # print(sentence) 
        if not result:
            tmp = word_tokenize(sentence)
            result.append(sentence)
            continue
        # when must concate when last sentence end by tail_words
        if tmp[-1] in tail_words:
            tmp = word_tokenize(sentence)
            result[-1] += " " + sentence
            continue
        # when must NOT concate when new sentence stard by header_words
        tmp = word_tokenize(sentence)
        # insert null string for null list to avoid error
        if len(tmp) == 0:
            tmp = [""]
        # when can split
        if (tmp[0] in header_words or len(result[-1]) > 200):  
            result.append(sentence)
            continue
        result[-1] += " " + sentence  
    result = '\n'.join(result)
    return result  

# the input is symbolic language solution
@timeout(120)
def check_answer(answer, proof, checker, score):
    if 'shows' not in answer:
        return False, "Autoformalization failed due to the conclusion is not in the translation."
    answer = answer.split('shows')
    if 'assumes' in answer[0]:
        header = answer[0].split('assumes')[0]
        assumptions = 'assumes' + answer[0].split('assumes')[1]
    else:
        header = answer[0]
        assumptions = ""
    conclusion = answer[1]
    
    quotes_pattern = re.compile(r'"([\s\S]*?)"')  
    header_match = quotes_pattern.findall(header)
    assumes_match = quotes_pattern.findall(assumptions)  
    shows_match = quotes_pattern.findall(conclusion)

    if float(score) < 0.8:
        message = "The Isabelle version is not consistent with the original problem (score < 0.8)."
        return False, message
    
    # check whether shows is in assumes
    if any((s in '\n'.join(assumes_match) or s in '\n'.join(header_match)) for s in shows_match):
        message = "Autoformalization failed due to the conclusion is in the assumptions."
        return False, message    
    
    # check whether shows is trivial
    for s in shows_match:
        # tmp = s.split(" = ")
        tmp = re.split(r'\s*=\s*|\\<le>\s*|\\<ge>\s*', s)
        if len(tmp) > 1 and tmp[0] == tmp[1]:
            message = "Autoformalization failed due to the conclusion is trivial."
            return False, message
    
    # whether assumptions introduced and used are consistent
    if len(assumes_match) > 0:
        lemmas_number = [f'h{i}' for i in range(len(assumes_match))]
        if any((s not in proof) for s in lemmas_number):
            message = "Assumptions in the translation is not consistent with the original problem."
            return False, message

    # check whether the assumptions are contradictory
    forall_pattern = r'\<forall> (.*?)\"'  
    exists_pattern = r'\<exists>! (.*?)\"'
    forall_match = re.findall(forall_pattern, assumptions)  
    exists_match = re.findall(exists_pattern, assumptions)
    if any(x in exists_match for x in forall_match):
        message = "Autoformalization failed due to the assumptions are contradictory."
        return False, message
    formal = header + assumptions + "shows \"0=1\"" + '\n proof-' + proof + '\n qed\nend'
    ok = checker.check(formal, "../test/tmp/temp_%s.thy" %(checker.id))
    if ok == True: # it proves a contradiction
        message = "Autoformalization failed due to the assumptions are contradictory."
        return False, message
    message = ""
    return True, message
        
# the input is symbolic language solution
def parse_equations(s):  
    eqn_pattern = re.compile(r'\"(.*)\"', flags=re.DOTALL)
    ## note: we need to handle the formula like --
    ## split the case1: have "eqn1" and "eqn2" by sledgehammer but avoid the case2: have "card {n. 10 \<le> n \<and> n \<le> 99 \<and> n div 10 = 6} = 10"
    parts = s.replace('\<and>', 'wedge').split('and') if 'and' in s else [s]  
    parts = [p.replace('wedge', '\<and>') for p in parts]
    result = [match for part in parts for match in re.findall(eqn_pattern, part)]  
    return result 

# the input is symbolic language solution
def normalize_statement(symbolic_problem):
    symbolic_problem = symbolic_problem.replace('”','"').replace('“', '"') 
    ## 
    if 'proof-' in symbolic_problem:
        symbolic_problem = symbolic_problem.split('proof-')[0]
    if 'proof -' in symbolic_problem:
        symbolic_problem = symbolic_problem.split('proof -')[0]
    if 'begin' in symbolic_problem:
        symbolic_problem = symbolic_problem.split('begin')[1]
    if 'shows' in symbolic_problem:
        ass_cons = symbolic_problem.split('shows')
        conclusion = 'shows ' + ass_cons[1]
        if 'assumes' in ass_cons[0]:
            header = ass_cons[0].split('assumes')[0]
            assumptions = ass_cons[0].split('assumes')[1]
            quotes_pattern = re.compile(r'"([\s\S]*?)"') 
            assumes_match = quotes_pattern.findall(assumptions)
            for (i, ass) in enumerate(assumes_match):
                if i == 0:
                    assumptions = f'assumes h{i} : ' + f'"{ass}"' + '\n'
                else:
                    assumptions += f'and h{i} : ' + f'"{ass}"' + '\n'
        else:
            header = ass_cons[0]
            assumptions = ""
            assumes_match = []
        symbolic_problem = header + assumptions + conclusion
    return symbolic_problem



# the input is natural language solution and symbolic language solution
def normalize_proof(natural_solution, symbolic_solution, remove_lastline=True):
    if remove_lastline:
        symbolic_solution = '\n'.join(symbolic_solution.split('\n')[0:-1]) + '\n'
    # temply normalize the natural solution
    temp_solution = natural_solution.replace('$', '')
    # normalize the symbolic solution
    symbolic_solution = symbolic_solution.replace('”','"').replace('“', '"')
    symbolic_solution = symbolic_solution.replace('show ?thesis sledgehammer', '')
    symbolic_solution = symbolic_solution.replace('show', 'have').replace('thus', 'have')
    symbolic_solution = symbolic_solution.replace('by sledgehammer', 'sledgehammer')         
    parsed_solution = []
    comment_pattern = re.compile(r'\(\*(.*?)\*\)', flags=re.DOTALL) 
    for s in symbolic_solution.split('\n'):
        if s == '':
            continue
        ## skip the comment step
        tmp = re.findall(comment_pattern, s)
        if not tmp:
            ## add the sledgehammer
            if 'have' in s and 'by' not in s and 'sledgehammer' not in s:
                s = s + " sledgehammer"
            ## parse the equation
            eqns = [e for e in parse_equations(s) if e != '']
            if len(eqns) == 0:
                continue
            ## We can add more rules here
            for eqn in eqns:
                new_eqn = copy.copy(eqn)
                new_eqn = new_eqn.replace('plus', '+').replace('minus', '-')
                new_eqn = new_eqn.replace('times', '*').replace('div', '/')
                new_eqn = new_eqn.replace('powr', '^')
                if not re.search(r'[a-zA-Z]', new_eqn):
                    try:
                        number = re.search(r'-?\d+(\.\d+)?', new_eqn).group()
                        new_eqn = new_eqn.replace(number, f'({number}::real)', 1)
                    except Exception as e:
                        print('The original equation is:', eqn)
                        print('Remove it as null')
                        new_eqn = ""
                        print('Error:' , e)
                new_eqn = new_eqn.replace(' ^ ', ' powr ')
                s = s.replace(eqn, new_eqn)
        # else:
            ## remove the additional reasoning step
            # if any(t[1:-1].replace('$','') not in temp_solution for t in tmp): 
                # print('additional reasoning have been removed', tmp)
                # break
        parsed_solution.append(s)

    parsed_solution = '\n'.join(parsed_solution)
    parsed_solution += '\n  show ?thesis sledgehammer'
    return parsed_solution

# the input is symbolic language solution
def parse_proof(proofs):
    proof = [t for t in proofs.split('\n') if t != ' ']
    total_lines = len(proof)
    nl_lines = 0
    fl_lines = 0
    sry_lines = 0
    is_comment = False
    for p in proof:
        if p.replace(' ','').startswith('(*'):
            is_comment = True
        if is_comment == True:
            nl_lines += 1
        else:
            fl_lines += 1
            if 'sorry' in p or ('(*' in p and '*)' in p):
                sry_lines += 1
        if is_comment==True and p.replace(' ','').endswith('*)'):
            is_comment = False
    return nl_lines, fl_lines, sry_lines