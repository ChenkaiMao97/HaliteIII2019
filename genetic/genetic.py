import subprocess
import random
# subprocess.call(["./myBash.sh","RETURN_COEFF=0.8 IGNORE_COEFF=0.05 EXPLORE_AGAIN=0.25 LOCAL_RANDOM_TO_DESTINATION=0.7 MAX_SHIP_SEED=0.4 MAX_DROP_OFF_SEED=0.035 MAX_ENERGY_POINTS=15 DISTANCE_TO_BUILD_DROPOFF=8 BIGFISH_AMOUNT=400 FIRST_BUILD_SHIP=100 SECOND_MONEY_FOR_PORT=120 THIRD_BUILD_PORT=180 FOUTRH_STOP_BUILD_PORT=320", \
				# "RETURN_COEFF=0.8 IGNORE_COEFF=0.05 EXPLORE_AGAIN=0.25 LOCAL_RANDOM_TO_DESTINATION=0.7 MAX_SHIP_SEED=0.4 MAX_DROP_OFF_SEED=0.035 MAX_ENERGY_POINTS=15 DISTANCE_TO_BUILD_DROPOFF=8 BIGFISH_AMOUNT=400 FIRST_BUILD_SHIP=100 SECOND_MONEY_FOR_PORT=120 THIRD_BUILD_PORT=180 FOUTRH_STOP_BUILD_PORT=320"])

def generateString():
	RETURN_COEFF = random.uniform(0.6,0.95)
	IGNORE_COEFF = random.uniform(0.05,0.3)
	EXPLORE_AGAIN = random.uniform(0.2,0.5)
	LOCAL_RANDOM_TO_DESTINATION = random.uniform(0.3,0.6)
	MAX_SHIP_SEED= random.uniform(0.4,0.7)
	MAX_DROP_OFF_SEED = random.uniform(0.03,0.07)
	MAX_ENERGY_POINTS = random.randint(3,20)
	DISTANCE_TO_BUILD_DROPOFF = random.randint(4,20)
	BIGFISH_AMOUNT=random.randint(200,800)
	FIRST_BUILD_SHIP=random.randint(80,130) 
	SECOND_MONEY_FOR_PORT=random.randint(130,180)
	THIRD_BUILD_PORT=random.randint(180,280)
	FOUTRH_STOP_BUILD_PORT=random.randint(280,350)

	mystring = \
			"RETURN_COEFF="+str(RETURN_COEFF)+\
			" IGNORE_COEFF="+str(IGNORE_COEFF)+\
			" EXPLORE_AGAIN="+str(EXPLORE_AGAIN)+\
			" LOCAL_RANDOM_TO_DESTINATION="+str(LOCAL_RANDOM_TO_DESTINATION)+\
			" MAX_SHIP_SEED="+str(MAX_SHIP_SEED)+\
			" MAX_DROP_OFF_SEED="+str(MAX_DROP_OFF_SEED)+\
			" MAX_ENERGY_POINTS="+str(MAX_ENERGY_POINTS)+\
			" DISTANCE_TO_BUILD_DROPOFF="+str(DISTANCE_TO_BUILD_DROPOFF)+\
			" BIGFISH_AMOUNT="+str(BIGFISH_AMOUNT)+\
			" FIRST_BUILD_SHIP="+str(FIRST_BUILD_SHIP)+\
			" SECOND_MONEY_FOR_PORT="+str(SECOND_MONEY_FOR_PORT)+\
			" THIRD_BUILD_PORT="+str(THIRD_BUILD_PORT)+\
			" FOUTRH_STOP_BUILD_PORT="+str(FOUTRH_STOP_BUILD_PORT)
	myDict = \
			{"RETURN_COEFF": RETURN_COEFF, "IGNORE_COEFF":IGNORE_COEFF, "EXPLORE_AGAIN":EXPLORE_AGAIN,\
			 "LOCAL_RANDOM_TO_DESTINATION":LOCAL_RANDOM_TO_DESTINATION, "MAX_SHIP_SEED":MAX_SHIP_SEED,\
			 "MAX_DROP_OFF_SEED":MAX_DROP_OFF_SEED,"MAX_ENERGY_POINTS":MAX_ENERGY_POINTS,\
			 "DISTANCE_TO_BUILD_DROPOFF":DISTANCE_TO_BUILD_DROPOFF,"BIGFISH_AMOUNT":BIGFISH_AMOUNT,\
			 "FIRST_BUILD_SHIP":FIRST_BUILD_SHIP,"SECOND_MONEY_FOR_PORT":SECOND_MONEY_FOR_PORT,\
			 "THIRD_BUILD_PORT":THIRD_BUILD_PORT,"FOUTRH_STOP_BUILD_PORT":FOUTRH_STOP_BUILD_PORT}

	return mystring,myDict

def cross(dict1,dict2):
	return	{"RETURN_COEFF": (dict1["RETURN_COEFF"]+dict2["RETURN_COEFF"])/2, \
			 "IGNORE_COEFF":(dict1["IGNORE_COEFF"]+dict2["IGNORE_COEFF"])/2,  \
			 "EXPLORE_AGAIN":(dict1["EXPLORE_AGAIN"]+dict2["EXPLORE_AGAIN"])/2, \
			 "LOCAL_RANDOM_TO_DESTINATION":(dict1["LOCAL_RANDOM_TO_DESTINATION"]+dict2["LOCAL_RANDOM_TO_DESTINATION"])/2, \
			 "MAX_SHIP_SEED":(dict1["MAX_SHIP_SEED"]+dict2["MAX_SHIP_SEED"])/2, \
			 "MAX_DROP_OFF_SEED":(dict1["MAX_SHIP_SEED"]+dict2["MAX_SHIP_SEED"])/2, \
			 "MAX_ENERGY_POINTS":int(dict1["MAX_ENERGY_POINTS"]+dict2["MAX_ENERGY_POINTS"])/2, \
			 "DISTANCE_TO_BUILD_DROPOFF":int(dict1["DISTANCE_TO_BUILD_DROPOFF"]+dict2["DISTANCE_TO_BUILD_DROPOFF"])/2, \
			 "BIGFISH_AMOUNT":int(dict1["BIGFISH_AMOUNT"]+dict2["BIGFISH_AMOUNT"])/2, \
			 "FIRST_BUILD_SHIP":int(dict1["FIRST_BUILD_SHIP"]+dict2["FIRST_BUILD_SHIP"])/2, \
			 "SECOND_MONEY_FOR_PORT":int(dict1["SECOND_MONEY_FOR_PORT"]+dict2["SECOND_MONEY_FOR_PORT"])/2, \
			 "THIRD_BUILD_PORT":int(dict1["THIRD_BUILD_PORT"]+dict2["THIRD_BUILD_PORT"])/2, \
			 "FOUTRH_STOP_BUILD_PORT":int(dict1["FOUTRH_STOP_BUILD_PORT"]+dict2["FOUTRH_STOP_BUILD_PORT"])/2}

def mutate(dict1):
	dict1["RETURN_COEFF"] += random.uniform(-0.05,0.05)
	dict1["IGNORE_COEFF"] += random.uniform(-0.05,0.05)
	dict1["EXPLORE_AGAIN"] += random.uniform(-0.1,0.1)
	dict1["LOCAL_RANDOM_TO_DESTINATION"] += random.uniform(-0.1,0.1)
	dict1["MAX_SHIP_SEED"] += random.uniform(-0.15,0.15)
	dict1["MAX_DROP_OFF_SEED"] += random.uniform(-0.02,0.02)
	dict1["MAX_ENERGY_POINTS"] += random.randint(-3,3)
	dict1["DISTANCE_TO_BUILD_DROPOFF"] += random.randint(-4,4)
	dict1["BIGFISH_AMOUNT"] += random.randint(-100,100)
	dict1["FIRST_BUILD_SHIP"] += random.randint(-20,20)
	dict1["SECOND_MONEY_FOR_PORT"] += random.randint(-20,20)
	dict1["THIRD_BUILD_PORT"] += random.randint(-20,20)
	dict1["FOUTRH_STOP_BUILD_PORT"] += random.randint(-20,20)
	return dict1


seeds = ['1546673720','1546673785','1546673864','1546673885','1546673905']
maxList = [(0,'a')]
for i in range(100):
	score1 = 0
	score2 = 0
	for seed in seeds:
		theStr1,theDict1 = generateString()
		theStr2,theDict2 = generateString()
		subprocess.call(["./myBash.sh",theStr1,theStr2,seed])
		with open("./bot-0.log") as f:
		    content = f.readlines()
		# you may also want to remove whitespace characters like `\n` at the end of each line
		score1 += int(content[-1].split(' ')[1])
		with open("./bot-1.log") as f:
		    content = f.readlines()
		# you may also want to remove whitespace characters like `\n` at the end of each line
		score2 += int(content[-1].split(' ')[1])
	if(len(maxList)<10):
		maxList.append((score1,theDict1))
	if(len(maxList)<10):
		maxList.append((score2,theDict2))
	if(score1>min(maxList)[0]):
		maxList[maxList.index(min(maxList))] = (score1,theDict1)
	if(score2>min(maxList)[0]):
		maxList[maxList.index(min(maxList))] = (score2,theDict2)
	if(i%10 == 0):
		print(maxList)



