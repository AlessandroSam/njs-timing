import os
import html

def postLogMessage(message):
    print(message)

carList = {}

def getCarName(car):
    # return car;
    try:
        if car not in carList:
            fname = os.getcwd() + '\\content\\cars\\' + car + '\\ui\\ui_car.json'
            postLogMessage('opening carinfo file ' + fname)
            f = open(fname)            
            # postLogMessage('file open OK');
            for line in f:
                postLogMessage('read line ' + line)
                if (line.find("name") == -1):
                    continue
                keyval = line.split(':');
                postLogMessage(keyval);
                postLogMessage(len(keyval));
                if len(keyval) > 1 and ('name' in keyval[0]):
                    carName = keyval[1][2:-3]
                    postLogMessage('Got car name ' + carName + ' from JSON');
                    carList[car] = carName
                    f.close()
                    return carName
            f.close()
        # carName = carList[car];
        carName = car
        postLogMessage('Got car name ' + carName + ' from dictionary');
        return carName;
    except Exception as e:        
        postLogMessage("Cannot retrieve car name from ui_car.json");
        print(e)
        return car;

if __name__ == '__main__':
	print(getCarName('ks_mazda_787b'));
