from bs4 import BeautifulSoup
import requests
import time
import sys
import csv
import os

MASTER_LIST = 0
LATEST_GENERATION = 8

OUTPUT_PATH = "./output/"
LOG_FILE = open(OUTPUT_PATH + "generated_files.txt", "w+")

MASTER_URL = "https://pokemondb.net/pokedex/all"
ITEMS_URL = "https://pokemondb.net/item/all"
ABILITIES_URL = "https://pokemondb.net/ability"

POKEDEX_URL = "https://pokemondb.net/pokedex/game/{0}"
POKEMON_URL = "http://pokemondb.net/{0}"
LEARNSET_URL = "http://pokemondb.net/{0}/moves/{1}"
STATS_URL = "https://pokemondb.net/pokedex/stats/gen{0}"
MOVES_URL = "http://pokemondb.net/move/generation/{0}"
EVOLUTION_URL = "http://pokemondb.net/evolution#evo-g{0}"

def log(msg) -> int:
    return LOG_FILE.write(msg)

def notify(msg) -> None:
    print(msg, end="", flush=True)
    return None

def getGenerationGames(generation: int) -> [str]:
    games_list = []

    if generation == 1: games_list = ["red-blue-yellow"]
    elif generation == 2: games_list = ["gold-silver-crystal"]
    elif generation == 3: games_list = ["ruby-sapphire-emerald",
                                      "firered-leafgreen"]
    elif generation == 4: games_list = ["diamond-pearl",
                                      "platinum",
                                      "heartgold-soulsilver"]
    elif generation == 5: games_list = ["black-white",
                                      "black-white-2"]
    elif generation == 6: games_list = ["x-y",
                                      "omega-ruby-alpha-sapphire"]
    elif generation == 7: games_list = ["sun-moon",
                                      "ultra-sun-ultra-moon",
                                      "lets-go-pikachu-eevee"]
    elif generation == 8: games_list = ["sword-shield"]
    
    return games_list

def getGamePokedex(gen: int) -> None:
    game_list = getGenerationGames(gen)

    output_directory = OUTPUT_PATH + "generation_{}/".format(gen)
    os.makedirs(output_directory, exist_ok=True)
    pkmn = []

    for game in game_list:
        url = POKEDEX_URL.format(game)
        
        output_path = output_directory + game.replace("-","_") + ".csv"
        output_file = open(output_path, "w+")
        output_writer = csv.writer(output_file, delimiter=',', quotechar='"')

        soup = BeautifulSoup(str(requests.get(url).content), "lxml")
        main_div = soup.find("div", class_="infocard-list")

        for div in main_div.find_all("div"):
            number = int((div.find("small").text).replace("#",""))
            name = div.find("a", class_="ent-name")
            types = []
            
            for t in div.find_all("a", class_="itype"):
                types += [t.text]
            
            types = "/".join(types)                

            output_writer.writerow([number, name.text, types])
            pkmn.append(name["href"])
            
            # debug
            # if len(pkmn) > 50: 
            #     break
        
        log("Created file: {}\n".format(output_path))
        output_file.close()

    notify("Parsing learnset for {} pokemon...\n".format(len(pkmn)))

    for p in pkmn: 
        # Get learnset for pokemon
        nurl = LEARNSET_URL.format(p, gen)
        nsoup = BeautifulSoup(str(requests.get(nurl).content), "lxml")
        
        pname = p.replace("/pokedex/", "")
        tabs = nsoup.find_all("a", class_="tabs-tab")
        headings = nsoup.find_all("h3")
        step = int(len(headings)/len(tabs))

        for i in range(0, len(tabs)):
            for j in range(0, step):
                k = j + (i * step)

                pre = tabs[i].text.replace("/", "_").replace(" ", "_").replace("\\'", "")
                title = headings[k].text.replace("learnt by ", "").replace(" ", "_").lower()

                tbody = headings[k].find_next("tbody")
                tpara = headings[k].find_next("p").text

                if " does not " in tpara or " cannot " in tpara: continue 
                # if not tbody: continue

                output_dir = "{}{}/{}/".format(output_directory, pre, pname).lower()
                os.makedirs(output_dir, exist_ok=True)
                
                output_path = (output_dir + title + ".csv").lower()
                output_file = open(output_path, "w+")
                output_writer = csv.writer(output_file, delimiter=',', quotechar='"')

                thead = headings[k].find_next("thead").find_all("th")

                #level_up, tm, hm
                if "level_up" in title or "tm" in title or "hm" in title:
                    output_writer.writerow([thead[0].text, thead[1].text, thead[2].text, 
                        thead[3].text, thead[4].text, thead[5].text])

                    for row in tbody.find_all("tr"):
                        cells = row.find_all("td")

                        output_writer.writerow([cells[0].text, cells[1].text, cells[2].text, 
                            cells[3]["data-sort-value"], cells[4].text.replace(r"\xe2\x80\x94", "-"),
                            cells[4].text.replace(r"\xe2\x80\x94", "-")])

                #egg, move_tutor
                elif "egg" in title or "move_tutor" in title:
                    output_writer.writerow([thead[0].text, thead[1].text, thead[2].text, 
                        thead[3].text, thead[4].text])

                    for row in tbody.find_all("tr"):
                        cells = row.find_all("td")

                        output_writer.writerow([cells[0].text, cells[1].text, cells[2]["data-sort-value"], 
                            cells[3].text.replace(r"\xe2\x80\x94", "-"), cells[4].text.replace(r"\xe2\x80\x94", "-")])

                #pre-evolution, transfer-only
                elif "pre-evolution" in title or "transfer-only" in title:
                    output_writer.writerow([thead[0].text, thead[1].text, thead[2].text, 
                        thead[3].text, thead[4].text, thead[5].text])

                    for row in tbody.find_all("tr"):
                        cells = row.find_all("td")

                        output_writer.writerow([cells[0].text, cells[1].text, cells[2]["data-sort-value"], 
                            cells[3].text.replace(r"\xe2\x80\x94", "-"), cells[4].text.replace(r"\xe2\x80\x94", "-"),
                            cells[5].text.replace("—", "-")])

                output_file.close()
                log("Created file: {}\n".format(output_path))

        notify(".")

    notify("\n")
    return None

def generatePokdedexFiles(gen: int) -> None: 
    # Get Pokedex for each game in selected generation
    getGamePokedex(gen)
    
    # Get evolution chart for generation
    # Get moves for current generation
    # Get stats for current generation

    return None

def genreateMasterList() -> None:
    output_directory = OUTPUT_PATH + "master/"
    os.makedirs(output_directory, exist_ok=True)

    #Master Pokemon list
    output_path = output_directory + "pokedex.csv"
    output_file = open(output_path, "w+")
    output_writer = csv.writer(output_file, delimiter=',', quotechar='"')

    soup = BeautifulSoup(str(requests.get(MASTER_URL).content), "lxml")
    table = soup.find("table", id="pokedex").find("tbody")

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        
        ptype = []
        for t in cells[2].find_all("a"):
            ptype += [t.string]
        ptype = "/".join(ptype)

        pname = cells[1].find("a", class_="ent-name").string
        pmega = cells[1].find("small", class_="text-muted")
        
        if pmega != None: 
            pname = pmega.string

        pnum = int(cells[0].find_all("span")[2].string)
        total = cells[3].string
        hp = cells[4].string
        attack = cells[5].string
        defense = cells[6].string
        spatk = cells[7].string
        spdef = cells[8].string

        # Get learnset for pokemon

        # output_file.write(csv_line)
        output_writer.writerow([pnum, pname, ptype,
            ":".join([total, hp, attack, defense, spatk, spdef])])

    # print("Created file:", output_path)
    log("Created file: {}\n".format(output_path))
    output_file.close()

    return None

def generateItemMasterList() -> None:
    output_directory = OUTPUT_PATH + "master/"
    os.makedirs(output_directory, exist_ok=True)

    # Master items list
    output_path = output_directory + "items" + ".csv"
    output_file = open(output_path, "w+")
    output_writer = csv.writer(output_file, delimiter=',', quotechar='"')

    soup = BeautifulSoup(str(requests.get(ITEMS_URL).content), "lxml")
    table = soup.find("tbody")

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        iname = cells[0].find("a", class_="ent-name").string
        icat = cells[1].string
        
        ieffect = cells[2].string or ""

        output_writer.writerow([iname, icat, ieffect])

    # print("Created file:", output_path)
    log("Created file: {}\n".format(output_path))
    output_file.close()

    return None

def generateAbilitiesMasterList() -> None:
    output_directory = OUTPUT_PATH + "master/"
    os.makedirs(output_directory, exist_ok=True)

    # Master items list
    output_path = output_directory + "abilities" + ".csv"
    output_file = open(output_path, "w+")
    output_writer = csv.writer(output_file, delimiter=',', quotechar='"')

    soup = BeautifulSoup(str(requests.get(ABILITIES_URL).content), "lxml")
    table = soup.find("tbody")

    for row in table.find_all("tr"):
        cells = row.find_all("td")

        aname = cells[0].find("a", class_="ent-name").string
        apokemon = cells[1].string
        agen = cells[3].string

        adesc = cells[2].string or ""
        output_writer.writerow([aname, apokemon, adesc, agen])

    # print("Created file:", output_path)
    log("Created file: {}\n".format(output_path))
    output_file.close()

    return None

if __name__ == "__main__":
    args = len(sys.argv)
    if args > 3 or args == 2:
        print("Usage: python generate.py [-g generation]")
        exit()

    elif args == 3 and sys.argv[1] == "-g":
        gen = int(sys.argv[2])

        if gen > 8 or gen < 0:
            print("Error: Supported generations are 0-8;")
            exit()

        if gen == 0:
            for i in range(1, LATEST_GENERATION + 1):
                generatePokdedexFiles(i)
        else:
            generatePokdedexFiles(gen)

    else: 
        # print("Generating master lists...")
        log("Generating master lists...\n")
        # genreateMasterList()
        # generateItemMasterList()
        generateAbilitiesMasterList()

    if LOG_FILE: LOG_FILE.close()