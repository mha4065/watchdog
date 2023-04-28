import requests, pymongo, re, config
import argparse
import sys
from time import sleep
from discord_webhook import DiscordWebhook, DiscordEmbed


platforms = ['hackerone', 'bugcrowd', 'intigriti', 'yeswehack']

PATTERN = r"(?:(?:https?|ftp):\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?::\d+)?(?:\/\S*)?"

PATH = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/"

def get_data(url:str):
    return requests.get(url).json()

def is_exist(collection: str, db) -> bool:
    if collection in db.list_collection_names():
        return True
    return False

def insert_db(database, data:dict, collection_name:str, mongo_uri:str):
    # Connect to MongoDB client
    client = pymongo.MongoClient(mongo_uri)

    # Select database and collection
    
    # if platform in db.list_collection_names():
    #     print("Already exists!")
    #     return
    
    db = client[database]
    if is_exist(collection_name, db):
        # print(f"{collection_name} already exists!")
        return
    
    collection = db[collection_name]

    # Insert data into collection
    try:
        collection.insert_many(data)
        print("Successfully added to DB.")
        return True
    except Exception as e:
        print(e)


def check_changes(mongo_uri, database, platform:str, notification:str, token:str, telegram_chatid = None):
    try:
        # Connect to MongoDB client
        client = pymongo.MongoClient(mongo_uri)

        # Select database and collection
        db = client[database]
        if platform == 'hackerone':
            collection = db["hackerone"]
            
            # get new data
            new_results = cleaner(get_data(PATH + "hackerone.json"), platform)
            for program in new_results:
                old_data = collection.find_one({"handle": program["handle"]})
                
                if old_data == None:
                    in_scopes = "\n".join(program["in_scope"])
                    push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program", notification, token, telegram_chatid)
                    collection.insert_one(program)
                    continue
                
                for in_scope in program["in_scope"]:
                    if in_scope not in old_data["in_scope"]:
                        collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                        push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope", notification, token, telegram_chatid)
                        print(f"new scope found! {in_scope}")
                
                if not config.no_out_scope:
                    for out_of_scope in program["out_of_scope"]:
                        if out_of_scope not in old_data["out_of_scope"]:
                            print(f"new out of scope found! out_of_scope")
                            push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope", notification, token, telegram_chatid)
                            collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": out_of_scope}})  
        elif platform == 'bugcrowd':
            collection = db["bugcrowd"]
            # get new data
            new_results = cleaner(get_data(PATH + "bugcrowd.json"), platform)
            for program in new_results:
                old_data = collection.find_one({"code": program["code"]})
                if old_data == None:
                    in_scopes = "\n".join(program["in_scope"])
                    push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program", notification, token, telegram_chatid)
                    # New program
                    collection.insert_one(program)
                    continue
                for in_scope in program["in_scope"]:
                    #print(in_scope)
                    if in_scope not in old_data["in_scope"]:
                        collection.update_one({"code": program["code"]}, {"$push": {"in_scope": in_scope}})
                        push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope", notification, token, telegram_chatid)
                        print(f"new scope found! {in_scope}")

                if not config.no_out_scope:
                    for out_of_scope in program["out_of_scope"]:
                        if out_of_scope not in old_data["out_of_scope"]:
                            push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope", notification, token, telegram_chatid)
                            collection.update_one({"code": program["code"]}, {"$push": {"out_of_scope": out_of_scope}})        
        elif platform == 'intigriti':
            collection = db["intigriti"]
            # get new data
            new_results = cleaner(get_data(PATH + "intigriti.json"), platform)
            for program in new_results:
                old_data = collection.find_one({"handle": program["handle"]})
                if old_data == None:
                    in_scopes = "\n".join(program["in_scope"])
                    push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program", notification, token, telegram_chatid)
                    collection.insert_one(program)
                    continue
                for in_scope in program["in_scope"]:
                    #print(in_scope)
                    if in_scope not in old_data["in_scope"]:
                        collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                        push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope", notification, token, telegram_chatid)
                if not config.no_out_scope:
                    for out_of_scope in program["out_of_scope"]:
                        if out_of_scope not in old_data["out_of_scope"]:
                            push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope", notification, token, telegram_chatid)
                            collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": out_of_scope}})
        elif platform == 'yeswehack':
            collection = db["yeswehack"]
            # get new data
            new_results = cleaner(get_data(PATH + "yeswehack.json"), platform)
            for program in new_results:
                old_data = collection.find_one({"slug": program["slug"]})
                if old_data == None:
                    in_scopes = "\n".join(program["in_scope"])
                    push(program["logo"], program["title"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program", notification, token, telegram_chatid)
                    collection.insert_one(program)
                    continue
                for in_scope in program["in_scope"]:
                    if in_scope not in old_data["in_scope"]:
                        collection.update_one({"slug": program["slug"]}, {"$push": {"in_scope": in_scope}})
                        push(program["logo"], program["title"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope", notification, token, telegram_chatid)
        else:
            pass
    except:
        print("An error has occurred.")
                

def cleaner(data:dict, platform:str):
    try:
        if platform == 'hackerone':
            programs = []
            for program in data:
                program_name = program["attributes"]["name"]
                program_handle = program["attributes"]["handle"]
                program_scopes = program["relationships"]["structured_scopes"]["data"]
                offers_bounties = program["attributes"]["offers_bounties"]
                if len(program_scopes) == 0:
                    continue
                programs_dict = {"name":program_name,
                                 "handle": program_handle,
                                 "offers_bounties": offers_bounties,
                                 "program_url": "https://hackerone.com/" + program_handle,
                                 "logo": program["attributes"]["profile_picture"],
                                 "in_scope": [],
                                 "out_of_scope": []}
                for x in program_scopes:
                    if x["attributes"]["eligible_for_submission"]:
                        if x["attributes"]["asset_identifier"] != None:
                            programs_dict["in_scope"].append(x["attributes"]["asset_identifier"])
                        else:
                            pass
                    else:
                        if not config.no_out_scope:
                            if x["attributes"]["asset_identifier"] != None:
                                programs_dict["out_of_scope"].append(x["attributes"]["asset_identifier"])
                            else:
                                pass
                        else:
                            pass
                programs.append(programs_dict)
            return programs
        elif platform == 'bugcrowd':
            programs = []
            for program in data:
                program_name = program["name"]
                program_code = program["code"]
                program_scopes = program["target_groups"]
                offers_bounties = True if program["license_key"] == "bug_bounty" else False
                program["license_key"]
                if len(program_scopes) == 0:
                    continue
                programs_dict = {"name":program_name,
                                 "offers_bounties": offers_bounties,
                                 "code": program_code,
                                 "program_url": "https://bugcrowd.com/" + program_code,
                                 "logo": program["logo"],
                                 "in_scope": [],
                                 "out_of_scope": []}
                for x in program_scopes:
                    if x["in_scope"] == True:
                        for y in x["targets"]:
                            if y["uri"] != None:
                                programs_dict["in_scope"].append(y["uri"])
                            elif y["name"] != None:
                                programs_dict["in_scope"].append(y["name"])
                            else:
                                pass
                    else:
                        if not config.no_out_scope:
                            for y in x["targets"]:
                                if y["name"] != None:
                                    programs_dict["out_of_scope"].append(y["name"])
                                elif y["uri"] != None:
                                    programs_dict["out_of_scope"].append(y["uri"])
                                else:
                                    pass
                        else:
                            pass
                programs.append(programs_dict)
            return programs
        elif platform == 'intigriti':
            programs = []
            for program in data:
                program_name = program["name"]
                program_company_handle = program["companyHandle"]
                program_handle = program["handle"]
                program_scopes = program["domains"]
                if len(program_scopes) == 0:
                    continue
                offers_bounties = True if program["maxBounty"]["value"] > 0 else False
                programs_dict = {"name":program_name,
                                 "offers_bounties": offers_bounties,
                                 "companyHandle": program_company_handle,
                                 "handle": program_handle,
                                 "program_url": "https://app.intigriti.com/programs/" + program_company_handle + "/" + program_handle,
                                 "logo": "https://bff-public.intigriti.com/file/" + program["logoId"],
                                 "in_scope": [],
                                 "out_of_scope": []}
                for x in program_scopes:
                    if x["description"] and 'Out of scope' in x["description"] and not config.no_out_scope:
                        # out of scope!
                        domains = re.findall(PATTERN, x["description"])
                        for domain in domains:
                            if domain != None:
                                programs_dict["out_of_scope"].append(domain)
                            else:
                                pass
                    else:
                        # in_scope!
                        if x["endpoint"] != None:
                            programs_dict["in_scope"].append(x["endpoint"])
                        else:
                            pass
                        
                programs.append(programs_dict)
            return programs
        elif platform == 'yeswehack':
            programs = []
            for program in data:
                program_title = program["title"]
                program_slug = program["slug"]
                program_scopes = program["scopes"]
                if len(program_scopes) == 0:
                    continue
                offers_bounties = True if program["bounty"] else False
                programs_dict = {"title":program_title,
                                 "offers_bounties": offers_bounties,
                                 "slug": program_slug,
                                 "program_url": "https://yeswehack.com/programs/" + program_slug,
                                 "logo": program["thumbnail"]["url"],
                                 "in_scope": [],
                                 "out_of_scope": []}
                for x in program_scopes:
                    if x["scope_type"] == "web-application":
                        if x["scope"] != None:
                            programs_dict["in_scope"].append(x["scope"])
                        else:
                            pass
                    else:
                        if not config.no_out_scope:
                            pass
                            # programs_dict["out_of_scope"].append(x["targets"]["name"])
                        else:
                            pass
                programs.append(programs_dict)
            return programs
        else:
            return
    except:
        print("An error has occurred !!!")
    

def push(logo_url, program_name, program_url, platform, message:str, bounty:bool, message_type:str, notification: str, token:str, telegram_chatid = None):
    if notification == "discord":
        try:
            webhook = DiscordWebhook(url=token)
            if platform == 'hackerone':
                embed = DiscordEmbed(title=message_type, description=message, color="ffffff")
                embed.set_thumbnail(url=logo_url)
                embed.add_embed_field(name="Platform:", value="Hackerone", inline=False)
            elif platform == 'bugcrowd':
                embed = DiscordEmbed(title=message_type, description=message, color="ff6900")
                embed.set_thumbnail(url=logo_url)
                embed.add_embed_field(name="Platform:", value="Bugcrowd", inline=False)
            elif platform == 'intigriti':
                embed = DiscordEmbed(title=message_type, description=message, color="4c59a8")
                embed.set_thumbnail(url=logo_url)
                embed.add_embed_field(name="Platform:", value="Intigriti", inline=False)
            elif platform == 'yeswehack':
                embed = DiscordEmbed(title=message_type, description=message, color="8f0e0e")
                embed.set_thumbnail(url=logo_url)
                embed.add_embed_field(name="Platform:", value="YesWeHack", inline=False)
            else:
                pass
            embed.add_embed_field(name="Program:", value=program_name, inline=False)
            embed.add_embed_field(name="Bounty:", value=bounty, inline=False)
            embed.add_embed_field(name="URL:", value=program_url, inline=False)             
            webhook.add_embed(embed)
            response = webhook.execute()
        except:
            print("Check your webhook")
    elif notification == "telegram":
        apiURL = f'https://api.telegram.org/bot{token}/sendMessage'

        msg = """
            {}
            {}
            Platform: {}
            Program: {}
            Bounty: {}
            URL: {}
        """.format(message_type, message, platform, program_name, bounty, program_url)

        try:
            response = requests.post(apiURL, json={'chat_id': telegram_chatid, 'text': msg})
        except Exception as e:
            print(e)
    else:
        print("[!] Unknown value for notification.")

def main():

    # Command-line arguments
    parser = argparse.ArgumentParser(description="A watcher script to watch for new changes in bugbounty platforms.",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-p", "--platforms", type=lambda arg: arg.replace(' ', '').split(','), default="all" ,help="Platforms to watch for (comma separated), 'all' for all platforms.")
    parser.add_argument("-t", "--telegram", action="store_true",help="Send notifications to Telegram.")
    parser.add_argument("-cid", help="Chat id of the telegram channel to send notifications to.")
    parser.add_argument("-d", "--discord", action="store_true", help="Send notifications to Discord.")
    parser.add_argument("--token", help="Telegram bot token OR Discord webhook.")
    parser.add_argument("--database", default=config.database,help="Database name.")
    parser.add_argument("--mongo", default="mongodb://mongo:27017/", help="MongoDB URI to connect.")
    args = parser.parse_args()
    arg_config = vars(args)
    # check if there is no command-line argument
    if len(sys.argv) > 1: #there is cmdline argumetns
        # Remove any databases in first run

        if len(arg_config["platforms"]) == 1 and arg_config["platforms"][0] == "all":
            input_platforms = platforms
        else:
            input_platforms = arg_config["platforms"]
        
        for platform in input_platforms:
            URL = PATH + platform + ".json"
            result = get_data(URL)
            clean_result = cleaner(result, platform)
            insert_db(arg_config["database"], clean_result, platform, arg_config["mongo"])

        for platform in input_platforms:
            if arg_config["telegram"]:
                check_changes(arg_config["mongo"], arg_config["database"], platform, "telegram", arg_config["token"], arg_config["cid"])
            else:
                check_changes(arg_config["mongo"], arg_config["database"], platform, "discord", arg_config["token"])
                
                
    else: # there is no commandline arguments so we sould get our configs from config file
        mongo_uri = "mongodb://"+config.mongoHost+":"+config.mongoPort+"/"
        
        if config.program == "all":
            input_platforms = platforms
        else:
            input_platforms = config.program.replace(' ', '').split(",")
        
        for platform in input_platforms:
            URL = PATH + platform + ".json"
            result = get_data(URL)
            clean_result = cleaner(result, platform)
            insert_db(config.database, clean_result, platform, mongo_uri)


        for platform in input_platforms:
            if config.telegram:
                check_changes(mongo_uri, config.database, platform, "telegram", config.telegram_token, config.telegram_chatid)
            else:
                check_changes(mongo_uri, config.database, platform, "discord", config.discord_webhook)


if __name__ == "__main__":
    main()