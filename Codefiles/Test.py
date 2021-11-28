import csv

file = open("../data/Node1.csv")
csvreader = csv.reader(file)

for row in csvreader:
    print("X-coordinate: ", row[0],  " Y:coordinate: ", row[1], " Speed:", row[2], " RadarF: ",
          row[3], " RadarB:",  row[4], " RadarL:",  row[5], " RadarR:",  row[6], " oxygen:", row[7])