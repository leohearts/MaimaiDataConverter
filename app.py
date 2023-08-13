import json
import csv
import coloredlogs, logging
from bs4 import BeautifulSoup
import argparse,sys
import os

def initMusicNameIdData(refreshCache, installPath):
    '''
    args refreshCache: int, installPath: str,
    returns Map<string, int>
    '''
    # use cache
    if os.path.exists("musicSortAll.json") and not refreshCache:
        return json.load(open("musicSortAll.json"))
    if not installPath:
        logging.error("No music id map data configured! Please specify --installPath (Sinmai_Data folder)")
        exit(-1)
    installPath = os.path.join(installPath, 'StreamingAssets')
    musicSortDataSourceList = [os.path.join('A000', 'music', 'MusicSort_backup.xml'),
                               os.path.join('A000', 'music', 'MusicSort.xml')]
    # always keep the right order as old entries may be overridden.
    musicXmlList = []
    returnsMap = {}
    for entry in musicSortDataSourceList:
        dataText = open(os.path.join(installPath, entry)).read()
        bs_data = BeautifulSoup(dataText, 'xml')
        for dataLine in bs_data.find_all('StringID'):
            id = int(dataLine.id.text)
            name = dataLine.str.text
            
            if name in returnsMap and returnsMap[name] != id:
                oldValue = returnsMap[name]
                logging.warning("Warning: dulplicate %s with different value %d %d, possibly a DX version and a Legacy version" % (name, oldValue, id))
                if name == 'Knight Rider': # some Sinmod shit, dont use existing name for modding :(
                    returnsMap[name] = max(oldValue, id)
                    continue
                returnsMap[name + "_Legacy"] = min(oldValue, id)
                returnsMap[name] = max(oldValue, id)
            else:
                returnsMap[name] = id
            logging.debug((entry, id, name))
    
    for root, dirs, files in os.walk(installPath):
        for file in files:
            if file == "Music.xml":
                xmlPath = os.path.join(root, file)
                musicXmlList.append(xmlPath)
    
    logging.info("found %d Music.xml" % len(musicXmlList))

    for entry in musicXmlList:
        dataText = open(os.path.join(installPath, entry)).read()
        bs_data = BeautifulSoup(dataText, 'xml')
        dataLine = bs_data.find("name")
        id = int(dataLine.id.text)
        name = dataLine.str.text
        if name in returnsMap and returnsMap[name] != id:
            oldValue = returnsMap[name]
            logging.warning("Warning: dulplicate %s with different value %d %d, possibly a DX version and a Legacy version" % (name, oldValue, id))
            if name == 'Knight Rider': # some community shit, please dont use existing name for modding :(
                returnsMap[name] = max(oldValue, id)
                continue
            returnsMap[name + "_Legacy"] = min(oldValue, id)
            returnsMap[name] = max(oldValue, id)
        else:
            returnsMap[name] = id
        logging.debug((entry, id, name))
    
    logging.info("found %d entries" % len(returnsMap))
    open("musicSortAll.json", "w").write(json.dumps(returnsMap))
    return returnsMap

def processMaimaiCsv(csvPath, musicNameIdData):
    '''
    args csvPath: str, musicNameIdData: Map<str, int>
    returns List<Object>
    '''
    if not csvPath:
        logging.error("No csv data! Please specify --csvPath (from maimaidx-prober, UTF-8)")
        exit(-1)
    returnsList = []
    for line in csv.reader(open(csvPath)):
        if line[0] == '曲名':
            continue
        targetObj = {}
        musicName = line[0]
        isNewVersion = True
        if musicName+"_Legacy" in musicNameIdData:
            isNewVersion = line[1] == "DX"
        musicLevel = line[2]
        achievement = line[5]
        deluxscoreMax = line[6]
        try:
            musicId = musicNameIdData[musicName] if isNewVersion else musicNameIdData[musicName + "_Legacy"]
        except KeyError as e:
            logging.error("Error: Missing %s , %s " % (musicName, str(e)))
        logging.debug((musicName, musicId, musicLevel, isNewVersion, achievement, deluxscoreMax))
        targetObj['musicId'] = musicId
        targetObj['level'] = {"Basic": 0, "Advanced": 1, "Expert": 2, "Master": 3, "Re:MASTER": 4}[musicLevel]
        targetObj['playCount'] = 1 # dummy
        targetObj['achievement'] = int(float(achievement) * 10000)
        targetObj['comboStatus'] = 0
        targetObj['syncStatus'] = 0 # maimaidx-prober won't include these to exported csv. 
        # TODO: provide an option to import data from /api/maimaidxprober/player/records. API may change.
        targetObj['deluxscoreMax'] = int(deluxscoreMax)
        scoreRank = 0
        rankingProcess = [50, 60, 70, 75, 80, 90, 94, 97, 98, 99, 99.5, 100, 100.5]
        for ranking in rankingProcess:
            if targetObj['achievement'] >= ranking * 10000:
                scoreRank += 1
        targetObj['scoreRank'] = scoreRank
        targetObj['extNum1'] = 0    # TODO: what's this?
        logging.debug(targetObj)
        returnsList.append(targetObj)
    logging.info("Processed %d lines" % len(returnsList))
    return returnsList

def mergeWithPreviousJson(jsonPath, newMusicItems):
    if not jsonPath:
        logging.error("No json data! Please specify --jsonPath (from your community server)")
        exit(-1)
    j = json.load(open(jsonPath))
    previousData = j['userMusicDetailList'].copy()
    for newData in newMusicItems:
        checkPreviousData = [i for i in previousData if i['musicId'] == newData['musicId'] and i['level'] == newData['level']]
        if checkPreviousData:
            # if pervious data exists, use the highest one 
            oldIndex = previousData.index(checkPreviousData[0])
            j['userMusicDetailList'][oldIndex]['playCount'] += 1
            j['userMusicDetailList'][oldIndex]['deluxscoreMax'] = max(j['userMusicDetailList'][oldIndex]['deluxscoreMax'], newData['deluxscoreMax'])
            j['userMusicDetailList'][oldIndex]['achievement'] = max(j['userMusicDetailList'][oldIndex]['achievement'], newData['achievement'])
            j['userMusicDetailList'][oldIndex]['scoreRank'] = max(j['userMusicDetailList'][oldIndex]['scoreRank'], newData['scoreRank'])
            logging.debug("Updating old entry: " + str(j['userMusicDetailList'][oldIndex]))
        else:
            j['userMusicDetailList'].append(newData)
    logging.info("Merge success. Before: %d songs, After: %d songs." % (len(previousData), len(j['userMusicDetailList'])))
    logging.debug(j['userMusicDetailList'])
    logging.info("Check out.json and import it to your server.")
    logging.info("Your server may take some time to process your request.")
    open("out.json", 'w').write(json.dumps(j))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=bool, default=False)
    parser.add_argument("--installPath", type=str)
    parser.add_argument("--refreshCache", type=bool, default=False)
    parser.add_argument("--csvPath", type=str)
    parser.add_argument("--jsonPath", type=str)
    args = parser.parse_args(sys.argv[1:])
    coloredlogs.install(level=(logging.DEBUG if args.debug else logging.INFO))
    # print(args)
    musicNameIdData = initMusicNameIdData(args.refreshCache, args.installPath)
    logging.info("loaded %d entries" % len(musicNameIdData))
    newMusicItems = processMaimaiCsv(args.csvPath, musicNameIdData)
    mergeWithPreviousJson(args.jsonPath, newMusicItems)
