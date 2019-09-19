names = []

#name_classes = ["scientific name", "equivalent name", "synonym"]
name_classes = ["common name"]

with open("names.dmp", "r") as handle:
    for line in handle:
        line = line.strip("\n").split("\t")
        line = [item for item in line if item != "|"]
        if line[3] in name_classes:
            names.append(line[1])

with open("org_list_common_names", "w") as out:
    for name in names:
        out.write("".join([name, "\n"]))

