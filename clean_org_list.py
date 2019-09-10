
orgs = []
chars = set(" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")

with open("org_list_all", "r") as handle:
    for line in handle:
        line = line.strip("\n")
        clean_org = "".join([letter for letter in line if letter in chars])
        orgs.append(clean_org)

with open("clean_org_list", "w") as out:
    for org in orgs:
        out.write("".join([org, "\n"]))
