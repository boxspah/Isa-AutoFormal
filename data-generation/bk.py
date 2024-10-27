def simplify_statement(checker, cxts, vars, assms):
    vars_list = []
    for term in vars.split("and"):
        vars_list += (term.split("::")[0].strip().split(" "))
    if DEBUG: print('checkpoint 4: parse vars', vars_list) # checkpoint 4
    formal = cxts + "\ntheorem" + "\nfixes " + vars + "\nassumes " + assms + "\nshows \"False\""
    ok, results = checker.simplify(formal, './tmp/temp.thy')
    if DEBUG: print('checkpoint 5: checker simplify', ok, results) # checkpoint 5
    num_goals = int(re.findall(r'goal \((\d+) subgoal\)', results)[0])
    match = re.search(rf'goal \({num_goals} subgoal\):(.*)At command "done"', results, re.DOTALL) 
    if match is None:
        raise NotImplementedError('No goals in the results', results)
    else:
        goals = match.group(1).strip().split("\n")
    #### remove 
    for i in range(num_goals):
        match = re.search(r'\\<lbrakk>(.*?)\\<rbrakk>', goals[i])
        conds = match.group(1).split("; ")
    dep_vars = ['answer']
    dep_assms = []
    for cond in conds[::-1]:
        if any(x in cond.split(' ') for x in dep_vars):
            dep_assms.append(cond)
            dep_vars += [t for t in cond.split(' ') if t not in dep_vars and t in vars_list]
    aux_vars = [item for item in vars_list if item not in dep_vars]
    aux_assms = [item for item in conds if item not in dep_assms]
    if DEBUG: print('checkpoint 6: clarify assms and vars', dep_vars, aux_vars, dep_assms, aux_assms)
    return dep_vars, aux_vars, dep_assms, aux_assms


def custom_edit_distance(assms0, assms1, vars):  
    # Initialize matrix of zeros     
    assms0 = assms0.split(' ')
    assms1 = assms1.split(' ')
    distances = np.zeros(shape=(len(assms0)+1, len(assms1)+1))  
    matched_vars = set()
    
    # Initialize first column and row  
    for i in range(len(assms0) + 1):  
        distances[i][0] = i  
    for j in range(len(assms1) + 1):  
        distances[0][j] = j  
  
    # Fill in the rest of the matrix  
    for i in range(1, len(assms0) + 1):  
        for j in range(1, len(assms1) + 1):  
            if assms0[i-1] == assms1[j-1] or (assms0[i-1] in vars and assms1[j-1] in vars):  
                distances[i, j] = distances[i-1, j-1]  
                if assms0[i-1] in vars and assms1[j-1] in vars:  
                    matched_vars.add((assms0[i-1], assms1[j-1])) 
            else:  
                distances[i, j] = min(  
                    distances[i-1, j] + 1,  # delete  
                    distances[i, j-1] + 1,  # insert  
                    distances[i-1, j-1] + 1  # substitute  
                )  
    return distances[-1, -1], matched_vars