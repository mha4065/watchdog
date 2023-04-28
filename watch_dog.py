import requests
import pymongo
import re
from time import sleep
from discord_webhook import DiscordWebhook, DiscordEmbed
import config
import argparse


platforms = ['hackerone', 'bugcrowd', 'intigriti', 'yeswehack']

PATTERN = r"(?:(?:https?|ftp):\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?::\d+)?(?:\/\S*)?"

HACKERONE = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/hackerone.json"
BUGCROWD = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/bugcrowd.json"
INTIGRITI = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/intigriti.json"
YESWEHACK = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/yeswehack.json"
PATH = "https://raw.githubusercontent.com/Osb0rn3/bugbounty-targets/main/programs/"

NOTIF_PLATFORM = []

def get_data(url:str):
    return requests.get(url).json()

def insert_db(data:dict, platform:str):
    # Connect to MongoDB client
    client = pymongo.MongoClient("mongodb://"+config.mongoHost+":"+config.mongoPort+"/")

    # Select database and collection
    db = client["bb_programs"]
    if platform in db.list_collection_names():
        print("Already exists!")
        return

    collection = db[platform]

    # Insert data into collection
    try:
        collection.insert_many(data)
        print("Successfully added to DB.")
        return True
    except Exception as e:
        print(e)


def check_changes(platform:str):
    # Connect to MongoDB client
    client = pymongo.MongoClient("mongodb://"+config.mongoHost+":"+config.mongoPort+"/")

    # Select database and collection
    db = client["bb_programs"]
    if platform == 'hackerone':
        collection = db["hackerone"]
        
        # get new data
        new_results = cleaner(get_data(HACKERONE), platform)
        for program in new_results:
            old_data = collection.find_one({"handle": program["handle"]})
            
            if old_data == None:
                in_scopes = "\n".join(program["in_scope"])
                push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program")
                collection.insert_one(program)
                continue
            
            for in_scope in program["in_scope"]:
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope")
                    print(f"new scope found! {in_scope}")
                    
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! out_of_scope")
                    push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope")
                    collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": out_of_scope}})
                    
    elif platform == 'bugcrowd':
        collection = db["bugcrowd"]
        # get new data
        new_results = cleaner(get_data(BUGCROWD), platform)
        for program in new_results:
            old_data = collection.find_one({"code": program["code"]})
            if old_data == None:
                in_scopes = "\n".join(program["in_scope"])
                push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program")
                # New program
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                #print(in_scope)
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"code": program["code"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope")
                    print(f"new scope found! {in_scope}")
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! out_of_scope")
                    push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope")
                    collection.update_one({"code": program["code"]}, {"$push": {"out_of_scope": out_of_scope}})
                    
    elif platform == 'intigriti':
        collection = db["intigriti"]
        # get new data
        new_results = cleaner(get_data(INTIGRITI), platform)
        for program in new_results:
            old_data = collection.find_one({"handle": program["handle"]})
            if old_data == None:
                in_scopes = "\n".join(program["in_scope"])
                push(program["logo"], program["name"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program")
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                #print(in_scope)
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"handle": program["handle"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["name"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope")
                    print(f"new scope found! {in_scope}")
            for out_of_scope in program["out_of_scope"]:
                if out_of_scope not in old_data["out_of_scope"]:
                    print(f"new out of scope found! out_of_scope")
                    push(program["logo"], program["name"], program["program_url"], platform, out_of_scope, program["offers_bounties"], "Out of Scope")
                    collection.update_one({"handle": program["handle"]}, {"$push": {"out_of_scope": out_of_scope}})
    
    elif platform == 'yeswehack':
        collection = db["yeswehack"]
        # get new data
        new_results = cleaner(get_data(YESWEHACK), platform)
        for program in new_results:
            old_data = collection.find_one({"slug": program["slug"]})
            if old_data == None:
                in_scopes = "\n".join(program["in_scope"])
                push(program["logo"], program["title"], program["program_url"], platform, in_scopes, program["offers_bounties"], "New Program")
                collection.insert_one(program)
                continue
            for in_scope in program["in_scope"]:
                if in_scope not in old_data["in_scope"]:
                    collection.update_one({"slug": program["slug"]}, {"$push": {"in_scope": in_scope}})
                    push(program["logo"], program["title"], program["program_url"], platform, in_scope, program["offers_bounties"], "New Scope")
                    print(f"new scope found! {in_scope}")
            # for out_of_scope in program["out_of_scope"]:
            #     if out_of_scope not in old_data["out_of_scope"]:
            #         print(f"new out of scope found! out_of_scope")
            #         collection.update_one({"slug": program["slug"]}, {"$push": {"out_of_scope": out_of_scope}})
    else:
        pass
                

def cleaner(data:dict, platform:str):
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
                    programs_dict["in_scope"].append(x["attributes"]["asset_identifier"])
                else:
                    programs_dict["out_of_scope"].append(x["attributes"]["asset_identifier"])
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
                        programs_dict["in_scope"].append(y["uri"])
                else:
                    for y in x["targets"]:
                        programs_dict["out_of_scope"].append(y["name"])
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
                if x["description"] and 'Out of scope' in x["description"]:
                    # out of scope!
                    domains = re.findall(PATTERN, x["description"])
                    for domain in domains:
                        programs_dict["out_of_scope"].append(domain)
                else:
                    # in_scope!
                    programs_dict["in_scope"].append(x["endpoint"])
                    
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
                    programs_dict["in_scope"].append(x["scope"])
                else:
                    # programs_dict["out_of_scope"].append(x["targets"]["name"])
                    pass
            programs.append(programs_dict)
        return programs
    else:
        return
    

def push(logo_url, program_name, program_url, platform, message:str, bounty:bool, type:str):
    webhook = DiscordWebhook(url=config.discord_webhook)
    if platform == 'hackerone':
        embed = DiscordEmbed(title=type, description=message, color="ffffff")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Platform:", value="Hackerone", inline=False)
        embed.add_embed_field(name="Program:", value=program_name, inline=False)
        embed.add_embed_field(name="Bounty:", value=bounty, inline=False)
        embed.add_embed_field(name="URL:", value=program_url, inline=False)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'bugcrowd':
        embed = DiscordEmbed(title=type, description=message, color="ff6900")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Platform:", value="Bugcrowd", inline=False)
        embed.add_embed_field(name="Program:", value=program_name, inline=False)
        embed.add_embed_field(name="Bounty:", value=bounty, inline=False)
        embed.add_embed_field(name="URL:", value=program_url, inline=False)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'intigriti':
        embed = DiscordEmbed(title=type, description=message, color="4c59a8")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Platform:", value="Intigriti", inline=False)
        embed.add_embed_field(name="Program:", value=program_name, inline=False)
        embed.add_embed_field(name="Bounty:", value=bounty, inline=False)
        embed.add_embed_field(name="URL:", value=program_url, inline=False)             
        webhook.add_embed(embed)
        response = webhook.execute()
    elif platform == 'yeswehack':
        embed = DiscordEmbed(title=type, description=message, color="8f0e0e")
        embed.set_thumbnail(url=logo_url)
        embed.add_embed_field(name="Platform:", value="YesWeHack", inline=False)
        embed.add_embed_field(name="Program:", value=program_name, inline=False)
        embed.add_embed_field(name="Bounty:", value=bounty, inline=False)
        embed.add_embed_field(name="URL:", value=program_url, inline=False)             
        webhook.add_embed(embed)
        response = webhook.execute()
    else:
        pass

def get_args():
    # Initializing Parser
    parser = argparse.ArgumentParser(description ='Config your Watch-dog')
      
    # Adding Argument
    parser.add_argument('-p', help='select the platform, H for HACKERONE, Y for YESWEHACK, I for INTIGRITI and B for Bugcrowd', dest='platform')
      
    
    args = parser.parse_args()
    platform = args.platform
    if "H" in platform:
        NOTIF_PLATFORM.append("hackerone")
    if "I" in platform:
        NOTIF_PLATFORM.append("intigriti")
    if "B" in platform:
        NOTIF_PLATFORM.append("bugcrowd")
    if "Y" in platform:
        NOTIF_PLATFORM.append("yeswehack")
    

def main():
    get_args()
    for platform in platforms:
        if platform in NOTIF_PLATFORM:
            URL = PATH + platform + ".json"
            result = get_data(URL)
            clean_result = cleaner(result, platform)
            insert_db(clean_result, platform)

    while True:
        sleep(5)
        for platform in platforms:
            if platform in NOTIF_PLATFORM:
                check_changes(platform)


if __name__ == "__main__":
    main()