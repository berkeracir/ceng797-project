fileNames = ["aggregated_accuracies.txt", "without_aggregated_accuracies.txt"]
folderNames = ["5-nodes-5-times-5-epoch-40-run", "10-nodes-5-times-5-epoch-40-run", "15-nodes-5-times-5-epoch-40-run"]

for folderName in folderNames:
    filePath = folderName

    for fileName in fileNames:
        path = filePath + "/" + fileName
        total = 0.0
        count = 0

        with open(path) as f:
            for line in f:
                total += float(line)
                count += 1
        print(f"{path} -> Average: {total/count}")
