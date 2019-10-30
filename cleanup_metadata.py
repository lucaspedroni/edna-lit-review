
metadata = []

with open("relevant_metadata_incl_barcoding_meshterm", "r") as handle:
    for line in handle:
        metadata.append(line.strip("\n").split("\t"))

pmids = [data[0] for data in metadata]
pmids = list(dict.fromkeys(pmids))

clean_metadata = []
for pmid in pmids:
    occurrences = [item for item in metadata if item[0] == pmid]
    if len(occurrences) > 1:
        added_flag = False
        for occurr in occurrences:
            if occurr[10] and not added_flag:
                clean_metadata.append(occurr)
                added_flag = True
        if not added_flag:
            clean_metadata.append(occurrences[0])
    else:
        clean_metadata.append(occurrences[0])

with open("clean_relevant_metadata_barcuid", "w") as out:
    for item in clean_metadata:
        out.write("\t".join(item))
        out.write("\n")
